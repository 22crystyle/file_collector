import os, logging
from typing import List, Set, Dict
from .constants import EXT2LANG

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
