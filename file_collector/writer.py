import os
from typing import List

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
