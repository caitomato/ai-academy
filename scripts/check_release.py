"""Enforce explicit versions and retain ID continuity against the prior release."""
import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bootstrap/scripts'))
from academy import fetch, version, STABLE_URL, Academy
from build_content import validate
import tempfile

v = sys.argv[1]
planned = json.loads((ROOT / 'content/release.json').read_text(encoding='utf-8-sig'))
if v != planned['version']:
    raise SystemExit('Tag version must match content/release.json')
version(v)
validate(ROOT / 'content')
try:
    prior = json.loads(fetch(STABLE_URL))
except urllib.error.HTTPError as error:
    if error.code != 404:
        raise
else:
    if version(v) <= version(prior['version']):
        raise SystemExit('Course versions must strictly increase')
    with tempfile.TemporaryDirectory() as tmp:
        academy = Academy(Path(tmp))
        academy.install(prior)
        from build_content import build_release
        manifest = build_release(ROOT / 'content', Path(tmp) / 'release', v)
        package = (Path(tmp) / 'release' / f'courses-{v}.zip').read_bytes()
        academy.download = lambda url: package
        academy.install(manifest)
print('Release contract verified', v)
