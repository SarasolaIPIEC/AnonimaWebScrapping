import textwrap
from pathlib import Path

path = Path('src/site/branch.py')
text = path.read_text(encoding='utf-8')


def replace_function(source: str, new_def: str) -> str:
    start = text.find(source)
    if start == -1:
        raise SystemExit(f'Function signature not found: {source}')
