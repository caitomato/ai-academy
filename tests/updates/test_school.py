import importlib.util
import json
import sys
import subprocess
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT/'bootstrap/scripts'))
from build_content import build_release, encode
from academy import Academy, STABLE_URL
from school import School


class LocalSchool(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root/'student'
        self.manifest = build_release(ROOT/'content', self.root/'release', '1.0.0')
        self.manifest['requiresConfirmation'] = False
        assets = {STABLE_URL: encode(self.manifest), self.manifest['packageUrl']: (self.root/'release/courses-1.0.0.zip').read_bytes()}
        self.academy = Academy(self.home, lambda url: assets[url])
        self.academy.check('first')
        self.school = School(self.home, 'first')
        self.spec = importlib.util.spec_from_file_location('installer', ROOT/'bootstrap/install.py')
        self.installer = importlib.util.module_from_spec(self.spec)
        self.spec.loader.exec_module(self.installer)

    def test_both_hosts_first_lesson_and_returning_student(self):
        for host in ('codex', 'claude'):
            with self.subTest(host=host):
                skill = self.installer.install(ROOT/'bootstrap', self.home, host, self.root/host/'skills')
                text = (Path(skill)/'SKILL.md').read_text(encoding='utf-8')
                self.assertNotIn('CORE_DIRECTORY', text)
                self.assertIn('name: ai-academy', text)
        self.assertEqual(self.school.start()['status'], 'onboarding')
        self.assertEqual(self.school.start()['lessonCount'], 90)
        self.school.enroll('coding','beginner')
        self.school.choose('06-01')
        self.school.record('phase','06-01','example:解释器')
        self.assertEqual(self.school.choose('06-01')['current']['position'], '解释器')
        self.school.record('note','06-01','解释器执行程序')
        self.school.answer('06-01','06-01-p1',['错误答案'])
        with self.assertRaises(ValueError): self.school.finish('06-01')
        for qid in [f'06-01-p{i}' for i in range(1,4)]+[f'06-01-t{i}' for i in range(1,5)]:
            q = self.school.question('06-01', qid)
            self.assertTrue(self.school.answer('06-01',qid,q['answer'])['correct'])
        with patch('school.Path.home', return_value=self.root):
            lab = self.school.lab('06-01')
            path = Path(lab['path'])/'hello.py'
            path.write_text('print("你好")\n',encoding='utf-8')
            output = subprocess.check_output([sys.executable, str(path)],encoding='utf-8')
            self.assertEqual(output.strip(), '你好')
            self.school.lab('06-01', '实际运行 hello.py：'+output.strip())
            self.school.lab('06-01')
            self.assertEqual(path.read_text(encoding='utf-8'),'print("你好")\n')
        self.assertEqual(self.school.finish('06-01')['score'],1)
        self.academy.check('second')
        state = School(self.home,'second').start()
        self.assertEqual(state['status'],'returning')
        self.assertIn('06-01',state['state']['completed'])
        self.assertIn('06-01-p1',state['state']['mistakes'])
        self.assertEqual(state['state']['notes']['06-01'],['解释器执行程序'])

    def test_backup_restore_and_reject_tampering(self):
        self.school.enroll('full','beginner')
        self.school.record('note','01-01','原笔记')
        destination = self.root/'backup.json'
        self.school.export(destination)
        self.school.record('note','01-01','新笔记')
        with self.assertRaises(ValueError): self.school.restore(destination)
        self.school.restore(destination,True)
        self.assertEqual(self.school.read()['notes']['01-01'],['原笔记'])
        saved = self.school.target.read_bytes()
        doc = json.loads(destination.read_text(encoding='utf-8'))
        doc['files']['school.json']['profile']['route']='tampered'
        destination.write_bytes(encode(doc))
        with self.assertRaises(ValueError): self.school.restore(destination,True)
        self.assertEqual(saved,self.school.target.read_bytes())

    def test_invalid_state_and_duplicate_lab_are_preserved(self):
        self.school.target.write_text('{broken',encoding='utf-8')
        with self.assertRaises(ValueError): self.school.enroll('coding','standard')
        self.assertEqual(self.school.target.read_text(encoding='utf-8'),'{broken')

    def test_uninstall_only_owned_entry(self):
        skill = Path(self.installer.install(ROOT/'bootstrap', self.home,'codex',self.root/'skills'))
        (skill/'personal.txt').write_text('keep')
        self.school.enroll('agent','standard')
        before = self.school.target.read_bytes()
        with self.assertRaises(ValueError): self.installer.uninstall(self.home,'codex')
        self.installer.uninstall(self.home,'codex',True)
        self.assertFalse((skill/'SKILL.md').exists())
        self.assertTrue((skill/'personal.txt').exists())
        self.assertEqual(before,self.school.target.read_bytes())

    def test_progressive_files_match_all_nine_chapters(self):
        root, index = self.school.curriculum()
        self.assertEqual(len(index),90)
        self.assertEqual({x['chapterId'] for x in index},set(range(1,10)))
        for item in index:
            original = json.loads((ROOT/'content/chapters'/('chapter%02d.json'%item['chapterId'])).read_text(encoding='utf-8'))
            lesson = next(x for x in original['lessons'] if x['id']==item['id'])
            self.assertGreater((root/item['lesson']).stat().st_size,100)
            assessment=json.loads((root/item['assessment']).read_text(encoding='utf-8'))
            self.assertEqual(assessment['questions'],lesson['questions'])
            self.assertEqual(assessment['test'],lesson['test'])

    def test_school_records_survive_new_lesson_update_and_failed_update(self):
        self.school.enroll('coding','beginner')
        self.school.record('note','06-01','保留我的笔记')
        self.school.answer('06-01','06-01-p1',['错误答案'])
        before = self.school.target.read_bytes()
        source = self.root/'new-source'
        shutil.copytree(ROOT/'content',source)
        chapter = json.loads((source/'chapters/chapter01.json').read_text(encoding='utf-8'))
        lesson = json.loads(json.dumps(chapter['lessons'][0]).replace('01-01','01-11'))
        chapter['lessons'].append(lesson)
        (source/'chapters/chapter01.json').write_bytes(encode(chapter))
        manifest = build_release(source,self.root/'v11','1.1.0')
        manifest['requiresConfirmation']=False
        assets={STABLE_URL:encode(manifest),manifest['packageUrl']:(self.root/'v11/courses-1.1.0.zip').read_bytes()}
        self.academy.download=lambda url: assets[url]
        self.assertEqual(self.academy.check('updated',force=True)['version'],'1.1.0')
        self.assertEqual(before,self.school.target.read_bytes())
        self.assertEqual(len(School(self.home,'updated').curriculum()[1]),91)
        def offline(url): raise OSError('offline')
        self.academy.download=offline
        self.assertEqual(self.academy.check('offline',force=True)['version'],'1.1.0')
        self.assertEqual(before,self.school.target.read_bytes())
        self.academy.rollback()
        self.assertEqual(self.academy.check('rolledback')['version'],'1.0.0')
        self.assertEqual(before,self.school.target.read_bytes())


if __name__ == '__main__': unittest.main()
