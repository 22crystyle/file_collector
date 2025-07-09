import os
import json
import logging
from typing import Dict, List, Set, Optional

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
        # старые defaults
        config.setdefault('overwrite_output', True)
        config.setdefault('overwrite_log', True)
        # новая опция
        config.setdefault('remove_imports', None)
        if config['remove_imports'] not in (None, 'all', 'non_static'):
            raise ValueError("Invalid 'remove_imports': must be 'all', 'non_static' or omitted")
        if 'start_path' not in config:
            raise ValueError("Missing required 'start_path' in config")
        config['start_path'] = os.path.normpath(config['start_path'])
        return config
    except Exception as e:
        logging.error(f"Config error: {str(e)}")
        raise

def normalize_paths(paths: List[str], base_path: str) -> List[str]:
    """Нормализация путей к абсолютному формату"""
    normalized = []
    for path in paths:
        if os.path.isabs(path):
            normalized.append(os.path.normpath(path))
        else:
            normalized.append(os.path.normpath(os.path.join(base_path, path)))
    return normalized

def is_excluded(path: str, exclude_dirs: List[str]) -> bool:
    """Проверка нахождения пути в исключённых директориях"""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(excl_dir) for excl_dir in exclude_dirs)

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
        for filename in files:
            file_path = os.path.join(root, filename)
            if check_ext:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue
            if filename not in collected:
                collected[filename] = file_path
                log_map[file_path] = source_tag
                logging.info(f"[{source_tag}] {filename} -> {file_path}")
    return list(collected.values())

def resolve_extra_files(
    file_list: List[str],
    base_path: str,
    exclude_dirs: List[str],
    log_map: Dict[str, str]
) -> List[str]:
    resolved = []
    for file_path in file_list:
        if os.path.isabs(file_path):
            abs_path = os.path.normpath(file_path)
            if os.path.isfile(abs_path) and not is_excluded(abs_path, exclude_dirs):
                resolved.append(abs_path)
                log_map[abs_path] = 'extra_abs'
                logging.info(f"[extra_abs] {os.path.basename(file_path)} -> {abs_path}")
            continue

        rel_path = os.path.normpath(os.path.join(base_path, file_path))
        if os.path.isfile(rel_path) and not is_excluded(rel_path, exclude_dirs):
            resolved.append(rel_path)
            log_map[rel_path] = 'extra_rel'
            logging.info(f"[extra_rel] {file_path} -> {rel_path}")
            continue

        found = False
        for root, _, files in os.walk(base_path):
            if is_excluded(root, exclude_dirs):
                continue
            if file_path in files:
                full_path = os.path.join(root, file_path)
                resolved.append(full_path)
                log_map[full_path] = 'extra_search'
                logging.info(f"[extra_search] {file_path} -> {full_path}")
                found = True
                break

        if not found:
            logging.warning(f"[missing] {file_path} not found")

    return resolved

def read_files(
    file_paths: List[str],
    base_dir: str,
    remove_imports: Optional[str] = None
) -> List[str]:
    """Чтение содержимого файлов с обёрткой в код-блоки, относительными путями и фильтрацией import"""
    contents = []
    for path in file_paths:
        # делаем относительный путь и заменяем обратные слеши
        try:
            rel_path = os.path.relpath(path, base_dir).replace('\\', '/')
        except ValueError:
            rel_path = path.replace('\\', '/')

        ext = os.path.splitext(path)[1].lower()
        lang = EXT2LANG.get(ext, '')
        fence = f"```{lang}" if lang else "```"
        header = f"File: {rel_path}"

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            # фильтрация import
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
            block = f"{header}\n```text\n// Error: File not found - {rel_path}\n```"
        except PermissionError:
            block = f"{header}\n```text\n// Error: Permission denied - {rel_path}\n```"
        except UnicodeDecodeError:
            block = f"{header}\n```text\n// Error: Encoding problem - {rel_path}\n```"
        except Exception as e:
            block = f"{header}\n```text\n// Error: {str(e)} - {rel_path}\n```"

        contents.append(block)
    return contents

def write_output(content: List[str], output_path: str, overwrite: bool = True) -> int:
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if not overwrite and os.path.exists(output_path):
        raise FileExistsError(f"Output file already exists: {output_path}")
    full_content = '\n\n'.join(content)
    line_count = len(full_content.split('\n'))
    with open(output_path, 'w' if overwrite else 'a', encoding='utf-8') as f:
        f.write(full_content)
    return line_count

def main():
    try:
        config = load_config('config.json')
        setup_logging(config.get('log_file', 'file_collector.log'), config['overwrite_log'])
        logging.info("=== File collection started ===")

        base_dir = config['start_path']
        exclude_dirs = normalize_paths(config.get('exclude_dirs', []), base_dir)
        extensions = {ext.lower() for ext in config.get('extensions', [])}

        log_map: Dict[str, str] = {}
        collected_files: List[str] = []

        if extensions:
            collected_files.extend(
                file_collector(base_dir, extensions, exclude_dirs, 'extension', log_map)
            )

        for include_dir in normalize_paths(config.get('include_all_from', []), base_dir):
            if os.path.isdir(include_dir):
                collected_files.extend(
                    file_collector(include_dir, set(), exclude_dirs, 'include_all', log_map, check_ext=False)
                )

        collected_files.extend(
            resolve_extra_files(config.get('extra_files', []), base_dir, exclude_dirs, log_map)
        )

        # убираем дубликаты по имени
        seen = set()
        unique_files = [f for f in collected_files if not (f in seen or seen.add(f))]

        content = read_files(unique_files, base_dir, config.get('remove_imports'))
        output_path = config.get('output_file', 'combined.txt')
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, 'combined.txt')

        try:
            line_count = write_output(content, output_path, config['overwrite_output'])
            logging.info(f"Successfully processed {len(unique_files)} files ({line_count} lines total)")
        except FileExistsError as e:
            logging.error(f"Error: {str(e)}. Use 'overwrite_output': true to overwrite.")

        logging.info("=== Operation completed successfully ===\n")

    except Exception as e:
        logging.error(f"!!! Operation failed: {str(e)} !!!")
        raise

if __name__ == '__main__':
    main()
