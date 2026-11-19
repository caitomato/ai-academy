import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'bootstrap/scripts'))
from build_content import build_release, validate, digest, encode
from academy import Academy, STABLE_URL, validate_manifest, fetch


class Server:
    def __init__(self):
        self.assets = {}
        self.calls = []
        self.offline = False

    def publish(self, source, output, version):
        manifest = build_release(source, output, version)
        self.assets[STABLE_URL] = encode(manifest)
        self.assets[manifest['packageUrl']] = (output / f'courses-{version}.zip').read_bytes()
        return manifest

    def __call__(self, url):
        self.calls.append(url)
        if self.offline:
            raise OSError('Simulated offline')
        return self.assets[url]


class UpdateContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'content'
        shutil.copytree(ROOT / 'content', self.source)
        self.server = Server()
        self.v1 = self.server.publish(self.source, self.root / 'v1', '1.0.0')

    def user(self, name):
        home = self.root / name
        (home / 'state').mkdir(parents=True)
        for kind, value in [('progress', {'06-10': {'completed': True}}), ('mistakes', {'06-10-p1': {'correct': False}}), ('notes', {'06-10': '函数学习笔记'}), ('mastery', {'06-10': 80})]:
            (home / 'state' / (kind + '.json')).write_bytes(encode(value))
        return Academy(home, self.server)

    def publish_v2(self):
        with (self.source / 'teaching/guide.md').open('a', encoding='utf-8') as f:
            f.write('\n复习时请学生先描述自己的预测，再检查实际运行结果。\n')
        return self.server.publish(self.source, self.root / 'v2', '1.1.0')

    def expire_cache(self, user):
        path = user.cache / 'latest-manifest.json'
        value = json.loads(path.read_text(encoding='utf-8'))
        value['checkedAt'] = 0
        path.write_bytes(encode(value))

    def test_three_students_update_offline_records_and_repeat(self):
        users = {name: self.user(name) for name in 'ABC'}
        snapshots = {n: {p.name: p.read_bytes() for p in (u.home / 'state').iterdir()} for n,u in users.items()}
        for user in users.values():
            self.assertEqual(user.check('session-1')['version'], '1.0.0')
        v2 = self.publish_v2()
        self.expire_cache(users['A'])
        self.assertEqual(users['A'].check('session-2')['version'], '1.1.0')
        self.assertEqual(users['B'].check('manual-new-session', force=True)['version'], '1.1.0')
        self.server.offline = True
        self.expire_cache(users['C'])
        self.assertEqual(users['C'].check('offline-session')['version'], '1.0.0')
        self.server.offline = False
        self.assertEqual(users['C'].check('reconnected-session')['version'], '1.1.0')
        count = self.server.calls.count(v2['packageUrl'])
        for user in users.values():
            self.assertFalse(user.check('another-session', force=True)['downloaded'])
        self.assertEqual(self.server.calls.count(v2['packageUrl']), count)
        for n,u in users.items():
            self.assertEqual({p.name: p.read_bytes() for p in (u.home / 'state').iterdir()}, snapshots[n])
        for item in v2['files']:
            self.assertEqual((users['A'].courses / '1.1.0' / item['path']).read_bytes(), (self.source / item['path']).read_bytes())

    def test_failure_keeps_old_version_and_explicit_rollback(self):
        user = self.user('A')
        user.check('one')
        v2 = self.publish_v2()
        good = self.server.assets[v2['packageUrl']]
        self.server.assets[v2['packageUrl']] = b'broken package'
        self.assertEqual(user.check('two', force=True)['status'], 'offline-or-update-failed')
        self.assertEqual(user.current()['version'], '1.0.0')
        self.assertFalse((user.courses / '1.1.0').exists())
        self.server.assets[v2['packageUrl']] = good
        user.check('three', force=True)
        self.assertEqual(user.rollback()['version'], '1.0.0')
        self.assertTrue((user.courses / '1.1.0').is_dir())
        self.assertEqual(user.check('after-rollback')['status'], 'rollback-held')

    def test_six_hour_cache_and_minimum_core(self):
        user = self.user('cache')
        user.check('one')
        requests = len(self.server.calls)
        user.check('one')
        user.check('two')
        self.assertEqual(len(self.server.calls), requests)
        manifest = self.publish_v2()
        manifest['minBootstrapVersion'] = '9.0.0'
        self.server.assets[STABLE_URL] = encode(manifest)
        response = user.check('three', force=True)
        self.assertEqual(response['version'], '1.0.0')
        self.assertIn('Bootstrap upgrade required', response['error'])

    def test_individual_hash_failure_even_when_zip_hash_matches(self):
        user = self.user('integrity')
        archive = self.root / 'changed.zip'
        original = self.root / 'v1/courses-1.0.0.zip'
        with zipfile.ZipFile(original) as source, zipfile.ZipFile(archive, 'w') as target:
            for name in source.namelist():
                data = source.read(name)
                if name == 'teaching/guide.md':
                    data = b'x' * len(data)
                target.writestr(name, data)
        body = archive.read_bytes()
        manifest = json.loads(encode(self.v1))
        manifest.update(sha256=digest(body), packageSize=len(body))
        self.server.assets[manifest['packageUrl']] = body
        with self.assertRaisesRegex(ValueError, 'file hash'):
            user.install(manifest)
        self.assertEqual(user.current(), {})

    def test_session_pinning_and_major_confirmation(self):
        user = self.user('A')
        user.check('ongoing')
        self.publish_v2()
        self.assertEqual(user.check('ongoing', force=True)['status'], 'deferred-until-new-session')
        self.assertEqual(user.current()['version'], '1.0.0')
        manifest = json.loads(self.server.assets[STABLE_URL])
        manifest['requiresConfirmation'] = True
        self.server.assets[STABLE_URL] = encode(manifest)
        self.assertEqual(user.check('new-major', force=True)['status'], 'confirmation-required')
        self.assertEqual(user.check('approved-new-session', force=True, accept_major=True)['version'], '1.1.0')

    def test_manifest_paths_origin_and_archive_mismatch(self):
        for path in ['../state/progress.json', '/etc/passwd', 'chapters/../../state/notes.json', 'chapters\\evil.json', 'chapters/CON.json']:
            bad = json.loads(encode(self.v1))
            bad['files'][0]['path'] = path
            with self.assertRaises(ValueError):
                validate_manifest(bad)
        bad = json.loads(encode(self.v1))
        bad['packageUrl'] = 'https://example.org/course.zip'
        with self.assertRaises(ValueError):
            validate_manifest(bad)
        user = self.user('bad')
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('../state/progress.json', '{}')
        body = archive.read_bytes()
        bad = json.loads(encode(self.v1))
        bad.update(sha256=digest(body), packageSize=len(body))
        self.server.assets[bad['packageUrl']] = body
        with self.assertRaises(ValueError):
            user.install(bad)
        self.assertEqual(user.current(), {})

    def test_missing_id_requires_migration(self):
        user = self.user('A')
        user.check('one')
        path = self.source / 'chapters/chapter06.json'
        chapter = json.loads(path.read_text(encoding='utf-8'))
        chapter['lessons'] = [l for l in chapter['lessons'] if l['id'] != '06-10']
        path.write_bytes(encode(chapter))
        manifest = self.server.publish(self.source, self.root / 'v2', '1.1.0')
        with self.assertRaisesRegex(ValueError, 'migration'):
            user.install(manifest)
        self.assertEqual(user.current()['version'], '1.0.0')

    def test_validation_rejects_broken_answer_and_duplicate_id(self):
        path = self.source / 'chapters/chapter01.json'
        c = json.loads(path.read_text(encoding='utf-8'))
        c['lessons'][0]['questions'][0]['answer'] = ['not an option']
        path.write_bytes(encode(c))
        with self.assertRaises(ValueError):
            validate(self.source)

    def test_installer_is_lightweight_and_separate(self):
        spec = importlib.util.spec_from_file_location('installer', ROOT / 'bootstrap/install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        home = self.root / 'installed'
        skills = self.root / 'skills'
        installer.install(ROOT / 'bootstrap', home, 'codex', skills)
        self.assertTrue((skills / 'ai-academy/SKILL.md').is_file())
        self.assertTrue((home / 'bootstrap/current.json').is_file())
        self.assertFalse((home / 'courses').exists())
        self.assertFalse((home / 'state').exists())
        before = (home / 'bootstrap/current.json').read_bytes()
        installer.install(ROOT / 'bootstrap', home, 'codex', skills)
        self.assertEqual((home / 'bootstrap/current.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
