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

VERSION = '2.0.0'
FILES = ['SKILL.md', 'launch.py', 'install.py', 'scripts/academy.py', 'scripts/state.py', 'scripts/school.py']
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
    required = FILES
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
    receipt = core.read_json(root / ('installed-' + host + '.json'), {})
    if skill_root:
        target_root = Path(skill_root)
    elif receipt.get('skill'):
        target_root = Path(receipt['skill']).parent
    elif host == 'codex' and (Path.home()/'.codex/skills/ai-academy/SKILL.md').exists():
        target_root = Path.home()/'.codex/skills'
    else:
        target_root = Path.home() / ('.agents/skills' if host == 'codex' else '.claude/skills')
    skill = target_root / 'ai-academy'
    skill.mkdir(parents=True, exist_ok=True)
    existing = skill / 'SKILL.md'
    if existing.exists() and (receipt.get('skill') != str(skill) or hashlib.sha256(existing.read_bytes()).hexdigest() != receipt.get('sha256')):
        # v1 had no receipt. Do not guess ownership or overwrite user changes.
        raise ValueError('目标 Skill 已存在且无匹配安装凭据。请先备份并移走该入口，或使用 --skill-root 选择新目录。')
    text = (source / 'SKILL.md').read_text(encoding='utf-8-sig')
    text = text.replace('~/.ai-academy', home.as_posix())
    text = text.replace('CORE_DIRECTORY', destination.as_posix())
    # Skill write is prepared before activation; course instructions are never embedded here.
    temporary = skill / 'SKILL.md.tmp'
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, skill / 'SKILL.md')
    core.atomic_json(root / 'current.json', dict(version=core_version))
    core.atomic_json(root / ('installed-' + host + '.json'), dict(skill=str(skill), sha256=hashlib.sha256((skill/'SKILL.md').read_bytes()).hexdigest()))
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
        allowed = set(FILES)
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


def uninstall(home, host, confirm=False):
    if not confirm:
        raise ValueError('卸载需要 --confirm；保留全部课程和学习记录。')
    core = core_module(BASE)
    receipt = core.read_json(Path(home) / 'bootstrap' / ('installed-' + host + '.json'), {})
    if not receipt: raise ValueError('没有安装凭据；不会删除未知文件。')
    target = Path(receipt['skill']) / 'SKILL.md'
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != receipt['sha256']:
            raise ValueError('Skill 已被修改，保留文件，请手动检查。')
        target.unlink()
    return '已卸载教学入口；课程、学习记录和实验文件均已保留。'


def rollback(home, host, skill_root=None, confirm=False):
    if not confirm: raise ValueError('核心回滚需要 --confirm；在新会话中使用。')
    core = core_module(BASE)
    previous = core.read_json(Path(home)/'bootstrap/previous.json', {})
    if not previous: raise ValueError('没有可回滚的核心。')
    core.version(previous['version'])
    source = Path(home)/'bootstrap/versions'/previous['version']
    if not (source/'scripts/school.py').exists():
        raise ValueError('旧核心不支持本地课堂，保留当前核心。可手动恢复旧安装包。')
    return install(source, home, host, skill_root, previous['version'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['codex', 'claude'])
    parser.add_argument('--home', type=Path, default=Path.home() / '.ai-academy')
    parser.add_argument('--skill-root', type=Path)
    parser.add_argument('--upgrade', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    if not args.host:
        args.host = 'claude' if input('安装到哪个工具？1 Codex / 2 Claude Code [1]：').strip() == '2' else 'codex'
    if args.rollback:
        print(rollback(args.home, args.host, args.skill_root, args.confirm))
    elif args.uninstall:
        print(uninstall(args.home, args.host, args.confirm))
    elif args.verify:
        core = core_module(BASE)
        receipt = core.read_json(args.home / 'bootstrap' / ('installed-'+args.host+'.json'), {})
        target = Path(receipt.get('skill',''))/'SKILL.md'
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=receipt.get('sha256'):
            raise SystemExit('安装验证失败，请重新安装或检查本地修改。')
        print('安装验证通过：'+str(target))
    else:
        print(upgrade(args.home, args.host, args.skill_root) if args.upgrade else install(BASE, args.home, args.host, args.skill_root))
