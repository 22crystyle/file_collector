import os
from typing import List
from .collector import EXT2LANG

def read_files(
    file_paths: List[str],
    base_dir: str,
    remove_imports: str = 'none'
) -> List[str]:
    contents = []
    for path in file_paths:
        try:
            rel = os.path.relpath(path, base_dir).replace('\\', '/')
        except ValueError:
            rel = path.replace('\\', '/')

        ext = os.path.splitext(path)[1].lower()
        lang = EXT2LANG.get(ext, '')
        fence = f"```{lang}" if lang else "```"
        header = f"File: {rel}"

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
