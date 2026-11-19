"""Build web assets and release packages from the sole content/ source."""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from skill_curriculum import generate
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'https://github.com/caitomato/ai-academy'
VERSION = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def validate(source):
    chapters = [json.loads(p.read_text(encoding='utf-8-sig')) for p in sorted((source / 'chapters').glob('*.json'))]
    if [c['id'] for c in chapters] != list(range(1, 10)):
        raise ValueError('Exactly nine numbered chapters required')
    lessons, questions = set(), set()
    for chapter in chapters:
        if not chapter.get('title') or not chapter.get('lessons'):
            raise ValueError('Empty chapter')
        for lesson in chapter['lessons']:
            lid = lesson['id']
            if lid in lessons or lesson['chapterId'] != chapter['id']:
                raise ValueError('Duplicate lesson or chapter mismatch: ' + lid)
            lessons.add(lid)
            for field in ('title', 'objectives', 'sections', 'example', 'task', 'steps'):
                if not lesson.get(field):
                    raise ValueError(f'Missing {lid}.{field}')
            if len(lesson['questions']) < 3 or not 3 <= len(lesson['test']) <= 5:
                raise ValueError('Incomplete question sets: ' + lid)
            for q in lesson['questions'] + lesson['test']:
                if q['id'] in questions or q['lessonId'] != lid:
                    raise ValueError('Question ID mismatch: ' + q['id'])
                questions.add(q['id'])
                if q['type'] not in ('single', 'multiple', 'boolean', 'fill', 'code', 'order'):
                    raise ValueError('Unknown question type')
                if not all(q.get(k) for k in ('prompt', 'answer', 'explanation')):
                    raise ValueError('Missing answer or explanation')
                if q['type'] != 'fill' and not set(q['answer']) <= set(q['options']):
                    raise ValueError('Answer outside options')
                if q['type'] in ('single', 'boolean', 'code') and len(q['answer']) != 1:
                    raise ValueError('Single choice must have one answer')
                if q['type'] == 'order' and sorted(q['answer']) != sorted(q['options']):
                    raise ValueError('Order answer must include all options')
            for resource in lesson.get('lab', {}).get('resources', []):
                href = resource['href']
                if href.startswith('./practice-kit/') and not (source / 'labs' / href.split('./practice-kit/', 1)[1]).is_file():
                    raise ValueError('Missing lab resource: ' + href)
            if lesson.get('experience', {}).get('kind') == 'node-project' and not (source / 'labs/study-timer.zip').is_file():
                raise ValueError('Node project download is missing')
    migrations = json.loads((source / 'migrations.json').read_text(encoding='utf-8-sig'))
    for kind, ids in [('lessonIds', lessons), ('questionIds', questions)]:
        for old, new in migrations[kind].items():
            if old in ids or new not in ids:
                raise ValueError('Invalid migration mapping')
    for name in ('guide.md', 'prompts.json'):
        if not (source / 'teaching' / name).is_file():
            raise ValueError('Missing teaching file')
    return chapters


def content_files(source):
    result = {}
    for folder in ('chapters', 'teaching', 'labs'):
        for p in sorted((source / folder).rglob('*')):
            if p.is_file():
                result[p.relative_to(source).as_posix()] = p.read_bytes()
    result['migrations.json'] = (source / 'migrations.json').read_bytes()
    result['CHANGELOG.md'] = (source / 'CHANGELOG.md').read_bytes()
    result.update(generate(validate(source)))
    return result


def zip_bytes(files, target):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def build_release(source, output, version=None, channel='stable'):
    validate(source)
    release = json.loads((source / 'release.json').read_text(encoding='utf-8-sig'))
    version = version or release['version']
    if not VERSION.fullmatch(version) or not VERSION.fullmatch(release['minBootstrapVersion']):
        raise ValueError('A numeric semantic version is required')
    output.mkdir(parents=True, exist_ok=True)
    files = content_files(source)
    package = output / f'courses-{version}.zip'
    zip_bytes(files, package)
    manifest = dict(product='AI Academy', channel=channel, version=version,
                    releaseDate=release['releaseDate'], minBootstrapVersion=release['minBootstrapVersion'],
                    requiresConfirmation=release.get('requiresConfirmation', False),
                    changelog=release['changelog'], added=release.get('added', []),
                    modified=release.get('modified', []), fixed=release.get('fixed', []),
                    packageUrl=f'{REPOSITORY}/releases/download/courses-v{version}/{package.name}',
                    sha256=digest(package.read_bytes()), packageSize=package.stat().st_size,
                    files=[dict(path=name, sha256=digest(data), size=len(data), lessonIds=[lesson['id'] for lesson in json.loads(data.decode('utf-8-sig'))['lessons']] if name.startswith('chapters/') else []) for name, data in sorted(files.items())])
    (output / 'manifest.json').write_bytes(encode(manifest))
    # Release asset read by the bootstrap; points to an immutable versioned package.
    (output / f'{channel}.json').write_bytes(encode(manifest))
    return manifest


def build_web(source=ROOT / 'content'):
    validate(source)
    for folder, destination in [('chapters', ROOT / 'src/data/curriculum'), ('labs', ROOT / 'public/practice-kit')]:
        destination.mkdir(parents=True, exist_ok=True)
        expected = {p.relative_to(source / folder).as_posix() for p in (source / folder).rglob('*') if p.is_file()}
        for old in destination.rglob('*'):
            if old.is_file() and old.relative_to(destination).as_posix() not in expected:
                old.unlink()
        for p in (source / folder).rglob('*'):
            if p.is_file():
                target = destination / p.relative_to(source / folder)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
    (ROOT / 'src/data/migrations.json').write_bytes((source / 'migrations.json').read_bytes())
    # Only published manifests are advertised as releases, never release plans.
    pointer = ROOT / 'updates/stable.json'
    public = ROOT / 'public/updates'
    public.mkdir(parents=True, exist_ok=True)
    if pointer.exists():
        shutil.copytree(ROOT / 'updates', public, dirs_exist_ok=True)
    metadata = json.loads(pointer.read_text(encoding='utf-8-sig')) if pointer.exists() else dict(version=None, releaseDate=None, changelog=[], added=[], modified=[], fixed=[])
    (ROOT / 'src/data/published-release.json').write_bytes(encode({k: metadata.get(k, []) for k in ('version', 'releaseDate', 'changelog', 'added', 'modified', 'fixed')}))
    download_dir = ROOT / 'public/downloads'
    download_dir.mkdir(parents=True, exist_ok=True)
    bootstrap_files = {p.relative_to(ROOT / 'bootstrap').as_posix(): p.read_bytes()
                       for p in (ROOT / 'bootstrap').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    zip_bytes(bootstrap_files, download_dir / 'ai-academy-bootstrap.zip')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release')
    parser.add_argument('--bootstrap-release')
    parser.add_argument('--channel', choices=['stable', 'beta'], default='stable')
    parser.add_argument('--output', type=Path, default=ROOT / 'release-output')
    args = parser.parse_args()
    if args.bootstrap_release:
        v = args.bootstrap_release
        if not VERSION.fullmatch(v):
            raise ValueError('Invalid bootstrap version')
        files = {name: (ROOT / 'bootstrap' / name).read_bytes() for name in ['SKILL.md', 'launch.py', 'install.py', 'scripts/academy.py', 'scripts/state.py', 'scripts/school.py']}
        args.output.mkdir(parents=True, exist_ok=True)
        package = args.output / f'bootstrap-{v}.zip'
        zip_bytes(files, package)
        manifest = dict(product='AI Academy Bootstrap', version=v, installerVersion='2.0.0', packageUrl=f'{REPOSITORY}/releases/download/bootstrap-v{v}/{package.name}', sha256=digest(package.read_bytes()), files=[dict(path=n, sha256=digest(b)) for n,b in sorted(files.items())])
        (args.output / 'bootstrap.json').write_bytes(encode(manifest))
    elif args.release:
        manifest = build_release(ROOT / 'content', args.output, args.release, args.channel)
        print(json.dumps(dict(version=manifest['version'], files=len(manifest['files']), sha256=manifest['sha256'])))
    else:
        build_web()
        print('Validated central curriculum; generated web and bootstrap assets.')


if __name__ == '__main__':
    main()
