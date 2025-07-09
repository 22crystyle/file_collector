import os
import json
import logging
from typing import Dict, List, Set

EXT2LANG = {
    '.java': 'java',
    '.md': 'markdown',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
}

def setup_logging(log_file: str, overwrite_log: bool = True) -> None:
    mode = 'w' if overwrite_log else 'a'
    handlers = [
        logging.FileHandler(log_file, encoding='utf-8', mode=mode),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=handlers
    )

def load_config(config_path: str) -> Dict:
    """Загрузка и валидация конфигурационного файла"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # defaults
        config.setdefault('overwrite_output', True)
        config.setdefault('overwrite_log', True)
        # новая опция
        config.setdefault('remove_imports', 'none')
        if config['remove_imports'] not in ('none', 'all', 'non_static'):
            raise ValueError("Invalid 'remove_imports': must be 'none', 'all' or 'non_static'")

        if 'start_path' not in config:
            raise ValueError("Missing required 'start_path' in config")
        config['start_path'] = os.path.normpath(config['start_path'])
        return config
    except Exception as e:
        logging.error(f"Config error: {e}")
        raise

def normalize_paths(paths: List[str], base_path: str) -> List[str]:
    normalized = []
    for path in paths:
        if os.path.isabs(path):
            normalized.append(os.path.normpath(path))
        else:
            normalized.append(os.path.normpath(os.path.join(base_path, path)))
    return normalized

def is_excluded(path: str, exclude_dirs: List[str]) -> bool:
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(excl) for excl in exclude_dirs)

def file_collector(
    root_dir: str,
    extensions: Set[str],
    exclude_dirs: List[str],
    source_tag: str,
    log_map: Dict[str, str],
    check_ext: bool = True
) -> List[str]:
    collected = {}
    for root, dirs, files in os.walk(root_dir):
        if is_excluded(root, exclude_dirs):
            dirs[:] = []
            continue
        for fn in files:
            path = os.path.join(root, fn)
            if check_ext:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in extensions:
                    continue
            if fn not in collected:
                collected[fn] = path
                log_map[path] = source_tag
                logging.info(f"[{source_tag}] {fn} -> {path}")
    return list(collected.values())

def resolve_extra_files(
    file_list: List[str],
    base_path: str,
    exclude_dirs: List[str],
    log_map: Dict[str, str]
) -> List[str]:
    resolved = []
    for fp in file_list:
        if os.path.isabs(fp):
            abs_p = os.path.normpath(fp)
            if os.path.isfile(abs_p) and not is_excluded(abs_p, exclude_dirs):
                resolved.append(abs_p)
                log_map[abs_p] = 'extra_abs'
                logging.info(f"[extra_abs] {os.path.basename(fp)} -> {abs_p}")
            continue

        rel_p = os.path.normpath(os.path.join(base_path, fp))
        if os.path.isfile(rel_p) and not is_excluded(rel_p, exclude_dirs):
            resolved.append(rel_p)
            log_map[rel_p] = 'extra_rel'
            logging.info(f"[extra_rel] {fp} -> {rel_p}")
            continue

        found = False
        for root, _, files in os.walk(base_path):
            if is_excluded(root, exclude_dirs):
                continue
            if fp in files:
                full_p = os.path.join(root, fp)
                resolved.append(full_p)
                log_map[full_p] = 'extra_search'
                logging.info(f"[extra_search] {fp} -> {full_p}")
                found = True
                break
        if not found:
            logging.warning(f"[missing] {fp} not found")
    return resolved

def read_files(
    file_paths: List[str],
    base_dir: str,
    remove_imports: str = 'none'
) -> List[str]:
    """Читает файлы, делает относительные пути, фильтрует импорты по need."""
    contents = []
    for path in file_paths:
        try:
            rel = os.path.relpath(path, base_dir).replace('\\', '/')
        except ValueError:
            rel = path.replace('\\', '/')

        ext = os.path.splitext(path)[1].lower()
        lang = EXT2LANG.get(ext, '')
        fence = f"```{lang}" if lang else "```"
        header = f"--- File: {rel} ---"

        try:
            lines = open(path, 'r', encoding='utf-8').read().splitlines()
            if remove_imports == 'all':
                lines = [l for l in lines if not l.lstrip().startswith('import ')]
            elif remove_imports == 'non_static':
                lines = [
                    l for l in lines
                    if not (l.lstrip().startswith('import ') and not l.lstrip().startswith('import static'))
                ]
            data = '\n'.join(lines).rstrip()
            block = "\n".join([header, fence, data, "```"])
        except FileNotFoundError:
            block = f"{header}\n```text\n// Error: File not found - {rel}\n```"
        except PermissionError:
            block = f"{header}\n```text\n// Error: Permission denied - {rel}\n```"
        except UnicodeDecodeError:
            block = f"{header}\n```text\n// Error: Encoding problem - {rel}\n```"
        except Exception as e:
            block = f"{header}\n```text\n// Error: {e} - {rel}\n```"

        contents.append(block)
    return contents

def write_output(content: List[str], output_path: str, overwrite: bool = True) -> int:
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    if not overwrite and os.path.exists(output_path):
        raise FileExistsError(f"Output file exists: {output_path}")
    full = '\n\n'.join(content)
    lines = full.split('\n')
    with open(output_path, 'w' if overwrite else 'a', encoding='utf-8') as f:
        f.write(full)
    return len(lines)

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

        # убрать дубликаты по имени
        seen = set()
        unique = [f for f in all_files if not (f in seen or seen.add(f))]

        logging.info(f"Собрано {len(unique)} файлов")
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
