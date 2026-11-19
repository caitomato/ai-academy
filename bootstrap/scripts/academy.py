"""Local-first course updater. Standard library only; never writes student state."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

BOOTSTRAP_VERSION = '1.0.0'
STABLE_URL = 'https://github.com/caitomato/ai-academy/releases/latest/download/stable.json'
SEMVER = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')
MAX_PACKAGE = 64 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version(value):
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise ValueError('Invalid semantic version')
    return tuple(map(int, value.split('.')))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default


def allowed_url(url):
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ''
    return (parsed.scheme == 'https' and not parsed.username and not parsed.password and
            (host in ('github.com', 'api.github.com', 'caitomato.github.io', 'release-assets.githubusercontent.com',
                      'objects.githubusercontent.com') or host.endswith('.githubusercontent.com')))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl):
            raise ValueError('Untrusted release redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, limit=MAX_PACKAGE):
    if not allowed_url(url):
        raise ValueError('Only official HTTPS GitHub distribution URLs are allowed')
    request = urllib.request.Request(url, headers={'User-Agent': 'AI-Academy-Bootstrap/1.0', 'Accept': 'application/octet-stream'})
    with urllib.request.build_opener(SafeRedirect()).open(request, timeout=25) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Download size limit exceeded')
    return data


def safe_path(name):
    if not isinstance(name, str) or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Unsafe file path')
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('Unsafe file path')
    if any(x.endswith(('.', ' ')) or x.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))} for x in p.parts):
        raise ValueError('Unsafe Windows file path')
    if p.parts[0] not in ('chapters', 'teaching', 'labs') and name not in ('migrations.json', 'CHANGELOG.md'):
        raise ValueError('Course package cannot write outside course content')
    return p


def validate_manifest(manifest):
    if manifest.get('product') != 'AI Academy' or manifest.get('channel') not in ('stable', 'beta'):
        raise ValueError('Unexpected product or channel')
    version(manifest['version'])
    version(manifest['minBootstrapVersion'])
    expected = f"https://github.com/caitomato/ai-academy/releases/download/courses-v{manifest['version']}/courses-{manifest['version']}.zip"
    if manifest['packageUrl'] != expected:
        raise ValueError('Package must belong to the official versioned repository release')
    if not re.fullmatch('[a-f0-9]{64}', manifest['sha256']):
        raise ValueError('Invalid package hash')
    if type(manifest.get('packageSize')) is not int or not 0 < manifest['packageSize'] <= MAX_PACKAGE:
        raise ValueError('Invalid package size')
    names = set()
    if not isinstance(manifest.get('files'), list) or not 1 <= len(manifest['files']) <= 10000:
        raise ValueError('Invalid file inventory')
    total = 0
    for item in manifest['files']:
        safe_path(item['path'])
        folded = item['path'].casefold()
        if folded in names or not re.fullmatch('[a-f0-9]{64}', item['sha256']):
            raise ValueError('Duplicate path or invalid file hash')
        names.add(folded)
        if type(item.get('size')) is not int or not 0 <= item['size'] <= MAX_PACKAGE:
            raise ValueError('Invalid file size')
        total += item['size']
    if total > MAX_PACKAGE:
        raise ValueError('Expanded package too large')
    required = {'migrations.json', 'teaching/guide.md', 'teaching/prompts.json'} | {f'chapters/chapter{i:02}.json' for i in range(1, 10)}
    if not required <= names:
        raise ValueError('Incomplete curriculum package')


def verify_directory(directory, manifest):
    for item in manifest['files']:
        p = directory / item['path']
        if not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != item['sha256']:
            raise ValueError('Course file missing or corrupt: ' + item['path'])


def validate_courses(directory):
    ids, questions = set(), set()
    for i in range(1, 10):
        chapter = read_json(directory / f'chapters/chapter{i:02}.json')
        if chapter['id'] != i or not chapter['lessons']:
            raise ValueError('Invalid chapter')
        for lesson in chapter['lessons']:
            if lesson['id'] in ids or lesson['chapterId'] != i:
                raise ValueError('Duplicate lesson ID')
            ids.add(lesson['id'])
            for q in lesson['questions'] + lesson['test']:
                if q['id'] in questions or q['lessonId'] != lesson['id'] or not q['answer'] or not q['explanation']:
                    raise ValueError('Invalid question')
                if q['type'] != 'fill' and not set(q['answer']) <= set(q['options']):
                    raise ValueError('Invalid answer')
                questions.add(q['id'])
    migrations = read_json(directory / 'migrations.json')
    for key, valid in [('lessonIds', ids), ('questionIds', questions)]:
        for old, new in migrations[key].items():
            if old in valid or new not in valid:
                raise ValueError('Invalid migration')
    return ids, questions


class Academy:
    def __init__(self, home, download=fetch):
        self.home = Path(home).expanduser().resolve()
        self.courses = self.home / 'courses'
        self.cache = self.home / 'cache'
        self.download = download
        for folder in (self.courses, self.cache):
            folder.mkdir(parents=True, exist_ok=True)
            if folder.is_symlink():
                raise ValueError('Managed directories cannot be symlinks')

    def current(self):
        return read_json(self.courses / 'current' / 'version.json', {})

    def activate(self, manifest):
        old = self.current()
        if old.get('version') != manifest['version'] and old:
            atomic_json(self.courses / 'previous.json', old)
        atomic_json(self.courses / 'current' / 'version.json', manifest)

    def install(self, manifest):
        validate_manifest(manifest)
        if version(manifest['minBootstrapVersion']) > version(BOOTSTRAP_VERSION):
            raise ValueError('Bootstrap upgrade required before installing this curriculum')
        destination = self.courses / manifest['version']
        if destination.exists():
            existing = read_json(destination / 'manifest.json')
            if existing != manifest:
                raise ValueError('Published versions are immutable; version collision')
            verify_directory(destination, manifest)
            validate_courses(destination)
            self.activate(manifest)
            return False
        data = self.download(manifest['packageUrl'])
        if len(data) != manifest['packageSize'] or sha(data) != manifest['sha256']:
            raise ValueError('Package SHA-256 or length mismatch')
        with tempfile.TemporaryDirectory(prefix='.staging-', dir=self.courses) as temporary:
            staging = Path(temporary)
            archive_path = staging / 'package.zip'
            archive_path.write_bytes(data)
            extracted = staging / 'content'
            extracted.mkdir()
            expected = {x['path']: x for x in manifest['files']}
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                if len(infos) != len(expected) or {i.filename for i in infos} != set(expected):
                    raise ValueError('ZIP inventory differs from manifest')
                for info in infos:
                    safe_path(info.filename)
                    if (info.external_attr >> 16) & 0o170000 == 0o120000 or info.flag_bits & 1:
                        raise ValueError('Symlinks and encrypted entries are not allowed')
                    item = expected[info.filename]
                    if info.file_size != item['size']:
                        raise ValueError('ZIP expanded length mismatch')
                    body = archive.read(info)
                    if sha(body) != item['sha256']:
                        raise ValueError('Course file hash mismatch')
                    path = extracted / info.filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(body)
            validate_courses(extracted)
            previous = self.current()
            if previous:
                old_dir = self.courses / previous['version']
                old_ids, old_questions = validate_courses(old_dir)
                new_ids, new_questions = validate_courses(extracted)
                migration = read_json(extracted / 'migrations.json')
                if not old_ids - new_ids <= set(migration['lessonIds']) or not old_questions - new_questions <= set(migration['questionIds']):
                    raise ValueError('Removed IDs need explicit migration mappings')
            atomic_json(extracted / 'manifest.json', manifest)
            os.replace(extracted, destination)
        self.activate(manifest)
        return True

    def check(self, session, force=False, accept_major=False):
        # Lock is held across download and activation; failed processes never affect current pointer.
        lock = self.courses / '.update.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return dict(status='busy', version=self.current().get('version'), message='Another update holds the lock; current curriculum remains usable.')
        try:
            os.close(fd)
            return self._check(session, force, accept_major)
        finally:
            lock.unlink(missing_ok=True)

    def _check(self, session, force, accept_major):
        current = self.current()
        session_key = sha(session.encode())
        pinned_file = self.cache / 'sessions' / (session_key + '.json')
        pinned = read_json(pinned_file)
        if pinned and not force:
            version(pinned['version'])
            pinned_manifest = read_json(self.courses / pinned['version'] / 'manifest.json')
            validate_manifest(pinned_manifest)
            verify_directory(self.courses / pinned['version'], pinned_manifest)
            return dict(status='session-pinned', version=pinned['version'], path=str(self.courses / pinned['version']))
        cache_file = self.cache / 'latest-manifest.json'
        try:
            cache = read_json(cache_file, {})
        except (ValueError, OSError):
            cache = {}
        try:
            if not force and time.time() - cache.get('checkedAt', 0) < 21600:
                manifest = cache['manifest']
            else:
                manifest = json.loads(self.download(STABLE_URL).decode('utf-8-sig'))
                validate_manifest(manifest)
                if manifest['channel'] != 'stable':
                    raise ValueError('Stable channel mismatch')
                atomic_json(cache_file, dict(checkedAt=time.time(), manifest=manifest))
            validate_manifest(manifest)
            hold = read_json(self.cache / 'rollback-hold.json', {})
            if current and hold and not force and version(manifest['version']) <= version(hold['rejectedVersion']):
                atomic_json(pinned_file, dict(version=current['version']))
                return dict(status='rollback-held', version=current['version'], path=str(self.courses / current['version']), latestVersion=manifest['version'])
            if current and version(manifest['version']) < version(current['version']):
                raise ValueError('Automatic downgrade refused; use explicit rollback')
            if current and current['version'] == manifest['version'] and current != manifest:
                raise ValueError('Released manifest changed without version increment')
            old_files = {x['path']: x['sha256'] for x in current.get('files', [])}
            changes = [x['path'] for x in manifest['files'] if old_files.get(x['path']) != x['sha256']]
            changed_lessons = set(lid for item in manifest['files'] if item['path'] in changes for lid in item.get('lessonIds', []))
            report = dict(currentVersion=current.get('version'), latestVersion=manifest['version'], changelog=manifest['changelog'], changedFiles=len(changes), affectedLessons=len(changed_lessons), message='检测到 AI Academy 有新版本。' if current.get('version') != manifest['version'] else '课程已是最新版本。')
            if pinned and manifest['version'] != pinned['version']:
                return dict(status='deferred-until-new-session', version=pinned['version'], path=str(self.courses / pinned['version']), **report)
            if manifest.get('requiresConfirmation') and current.get('version') != manifest['version'] and not accept_major:
                if current:
                    atomic_json(pinned_file, dict(version=current['version']))
                return dict(status='confirmation-required', version=current.get('version'), path=str(self.courses / current['version']) if current else None, **report)
            downloaded = self.install(manifest)
            atomic_json(pinned_file, dict(version=manifest['version']))
            return dict(status='updated' if downloaded else 'current', version=manifest['version'], path=str(self.courses / manifest['version']), downloaded=downloaded, **report)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
            if not current:
                return dict(status='unavailable', error=str(exc), message='First use requires an online curriculum download.')
            verify_directory(self.courses / current['version'], current)
            # Failed checks are not cached; a NEW session retries as soon as network returns.
            cache_file.unlink(missing_ok=True)
            atomic_json(pinned_file, dict(version=current['version']))
            return dict(status='offline-or-update-failed', version=current['version'], path=str(self.courses / current['version']), error=str(exc))

    def rollback(self):
        previous = read_json(self.courses / 'previous.json')
        if not previous:
            raise ValueError('No previous version available')
        verify_directory(self.courses / previous['version'], previous)
        validate_courses(self.courses / previous['version'])
        rejected = self.current()
        self.activate(previous)
        atomic_json(self.cache / 'rollback-hold.json', dict(rejectedVersion=rejected['version']))
        return dict(status='rolled-back', version=previous['version'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['start', 'check', 'rollback', 'status'])
    parser.add_argument('--home', type=Path, default=Path.home() / '.ai-academy')
    parser.add_argument('--session', default=None)
    parser.add_argument('--accept-major', action='store_true')
    args = parser.parse_args()
    academy = Academy(args.home)
    if args.command in ('start', 'check'):
        if not args.session:
            parser.error('--session must be the stable current conversation ID')
        result = academy.check(args.session, force=args.command == 'check', accept_major=args.accept_major)
    elif args.command == 'rollback':
        result = academy.rollback()
    else:
        result = dict(version=academy.current().get('version'), home=str(academy.home))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get('status') == 'unavailable':
        sys.exit(1)


if __name__ == '__main__':
    main()
