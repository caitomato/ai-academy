"""Install or safely upgrade only Bootstrap; never edit courses or student state."""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

VERSION = '1.0.0'
BASE = Path(__file__).resolve().parent


def core_module(base):
    spec = importlib.util.spec_from_file_location('academy_core', base / 'scripts/academy.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install(source, home, host, skill_root=None, core_version=VERSION):
    home = Path(home).expanduser().resolve()
    root = home / 'bootstrap'
    root.mkdir(parents=True, exist_ok=True)
    destination = root / 'versions' / core_version
    destination.parent.mkdir(parents=True, exist_ok=True)
    core = core_module(source)
    core.version(core_version)
    required = ['SKILL.md', 'launch.py', 'install.py', 'scripts/academy.py', 'scripts/state.py']
    for name in required:
        if not (source / name).is_file():
            raise ValueError('Incomplete bootstrap: ' + name)
    # Side-by-side core versions; stable launcher and prior core remain usable.
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix='.install-', dir=root) as tmp:
            stage = Path(tmp) / 'core'
            stage.mkdir()
            for name in required:
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / name, target)
            os.replace(stage, destination)
    else:
        for name in required:
            if (destination / name).read_bytes() != (source / name).read_bytes():
                raise ValueError('Bootstrap version collision; increment core version')
    if not (root / 'launch.py').exists():
        shutil.copyfile(source / 'launch.py', root / 'launch.py')
    if not (root / 'install.py').exists():
        shutil.copyfile(source / 'install.py', root / 'install.py')
        (root / 'scripts').mkdir(exist_ok=True)
        shutil.copyfile(source / 'scripts/academy.py', root / 'scripts/academy.py')
    current = core.read_json(root / 'current.json', {})
    if current and current.get('version') != core_version:
        core.atomic_json(root / 'previous.json', current)
    target_root = Path(skill_root) if skill_root else Path.home() / ('.codex/skills' if host == 'codex' else '.claude/skills')
    skill = target_root / 'ai-academy'
    skill.mkdir(parents=True, exist_ok=True)
    text = (source / 'SKILL.md').read_text(encoding='utf-8-sig')
    text = text.replace('~/.ai-academy', home.as_posix())
    # Skill write is prepared before activation; course instructions are never embedded here.
    temporary = skill / 'SKILL.md.tmp'
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, skill / 'SKILL.md')
    core.atomic_json(root / 'current.json', dict(version=core_version))
    return str(skill)


def upgrade(home, host, skill_root=None):
    core = core_module(BASE)
    manifest = json.loads(core.fetch('https://caitomato.github.io/ai-academy/updates/bootstrap.json'))
    v = manifest['version']
    core.version(v)
    expected = f'https://github.com/caitomato/ai-academy/releases/download/bootstrap-v{v}/bootstrap-{v}.zip'
    if manifest['packageUrl'] != expected:
        raise ValueError('Unexpected bootstrap release origin')
    installed = core.read_json(Path(home) / 'bootstrap/current.json', {})
    if installed and core.version(v) <= core.version(installed['version']):
        return 'Bootstrap already current.'
    body = core.fetch(expected)
    if hashlib.sha256(body).hexdigest() != manifest['sha256']:
        raise ValueError('Bootstrap package hash mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        archive = root / 'bootstrap.zip'
        archive.write_bytes(body)
        allowed = {'SKILL.md', 'launch.py', 'install.py', 'scripts/academy.py', 'scripts/state.py'}
        inventory = {x['path']: x['sha256'] for x in manifest['files']}
        if set(inventory) != allowed:
            raise ValueError('Unexpected bootstrap files')
        source = root / 'source'
        with zipfile.ZipFile(archive) as z:
            if len(z.infolist()) != len(allowed) or set(z.namelist()) != allowed:
                raise ValueError('Unexpected archive inventory')
            for info in z.infolist():
                if info.file_size > 1024 * 1024 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Invalid core file')
                data = z.read(info)
                if hashlib.sha256(data).hexdigest() != inventory[info.filename]:
                    raise ValueError('Bootstrap file hash mismatch')
                target = source / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        return install(source, home, host, skill_root, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['codex', 'claude'], required=True)
    parser.add_argument('--home', type=Path, default=Path.home() / '.ai-academy')
    parser.add_argument('--skill-root', type=Path)
    parser.add_argument('--upgrade', action='store_true')
    args = parser.parse_args()
    print(upgrade(args.home, args.host, args.skill_root) if args.upgrade else install(BASE, args.home, args.host, args.skill_root))
