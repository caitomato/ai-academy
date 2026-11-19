"""Generate production web courses from the exact current public Release package."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bootstrap/scripts'))
from academy import Academy, STABLE_URL, fetch, validate_manifest
from build_content import build_web, encode

manifest = json.loads(fetch(STABLE_URL))
validate_manifest(manifest)
with tempfile.TemporaryDirectory() as tmp:
    academy = Academy(Path(tmp))
    academy.install(manifest)
    pointer = ROOT / 'updates/stable.json'
    pointer.parent.mkdir(exist_ok=True)
    pointer.write_bytes(encode(manifest))
    build_web(academy.courses / manifest['version'])
print('Production web courses match published version', manifest['version'])
