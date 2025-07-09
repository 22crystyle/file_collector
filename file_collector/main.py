import os, logging
from .config import load_config, setup_logging
from .collector import (
    file_collector,
    resolve_extra_files,
    normalize_paths,  # ← добавить это
)
from .formatter import read_files
from .writer import write_output
from typing import Dict, List, Set

def main():
    try:
        cfg = load_config('config.json')
        setup_logging(cfg.get('log_file', 'file_collector.log'), cfg['overwrite_log'])
        logging.info("=== File collection started ===")

        base = cfg['start_path']
        excl = normalize_paths(cfg.get('exclude_dirs', []), base)
        exts = {e.lower() for e in cfg.get('extensions', [])}

        log_map: Dict[str, str] = {}
        all_files: List[str] = []

        if exts:
            all_files += file_collector(base, exts, excl, 'extension', log_map)
        for inc in normalize_paths(cfg.get('include_all_from', []), base):
            if os.path.isdir(inc):
                all_files += file_collector(inc, set(), excl, 'include_all', log_map, check_ext=False)
        all_files += resolve_extra_files(cfg.get('extra_files', []), base, excl, log_map)

        # убираем дубликаты по имени
        seen = set()
        unique = [f for f in all_files if not (f in seen or seen.add(f))]

        # --- лог сбора убран ---

        content = read_files(unique, base, cfg.get('remove_imports', 'none'))

        outp = cfg.get('output_file', 'combined.txt')
        if os.path.isdir(outp):
            outp = os.path.join(outp, 'combined.txt')

        try:
            cnt = write_output(content, outp, cfg['overwrite_output'])
            logging.info(f"Обработано {len(unique)} файлов ({cnt} строк)")
        except FileExistsError as e:
            logging.error(f"{e}. Используйте overwrite_output=true чтобы перезаписать.")

        logging.info("=== Завершено успешно ===")
    except Exception as e:
        logging.error(f"!!! Ошибка: {e} !!!")
        raise

if __name__ == '__main__':
    main()
