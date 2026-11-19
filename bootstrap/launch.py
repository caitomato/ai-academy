"""Stable launcher: choose installed core without replacing running sessions."""
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
pointer = json.loads((root / 'current.json').read_text(encoding='utf-8'))
core = root / 'versions' / pointer['version'] / 'scripts' / 'academy.py'
if not core.is_file() or root not in core.resolve().parents:
    raise SystemExit('Bootstrap core is unavailable; rerun the installer or restore previous.json.')
arguments = sys.argv[1:]
if '--home' not in arguments:
    arguments += ['--home', str(root.parent)]
raise SystemExit(subprocess.call([sys.executable, str(core), *arguments]))
