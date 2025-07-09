import os, json, logging

def setup_logging(log_file: str, overwrite_log: bool):
    mode = 'w' if overwrite_log else 'a'
    handlers = [
        logging.FileHandler(log_file, mode=mode, encoding='utf-8'),
        logging.StreamHandler()
    ]
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=handlers)

def load_config(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    cfg.setdefault('overwrite_output', True)
    cfg.setdefault('overwrite_log', True)
    cfg.setdefault('remove_imports', 'none')
    if cfg['remove_imports'] not in ('none','all','non_static'):
        raise ValueError("Invalid remove_imports")
    if 'start_path' not in cfg:
        raise ValueError("Missing start_path")
    cfg['start_path'] = os.path.normpath(cfg['start_path'])
    return cfg
