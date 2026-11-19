"""Local teaching session and student records. No network or model calls."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from academy import read_json, atomic_json, version

ROUTES = ('full', 'agent', 'coding', 'creative')
LEVELS = ('beginner', 'standard', 'advanced')
PHASES = ('explain', 'example', 'understand', 'practice', 'quiz', 'review')


def initial():
    return dict(schemaVersion=2, profile={}, current=None, completed={}, skipped=[],
                attempts=[], mastery={}, mistakes={}, notes={}, bookmarks=[], weakPoints=[],
                labs={}, recommendation=None, lastLearningAt=None)


def validate(data):
    prototype = initial()
    if not isinstance(data, dict) or data.get('schemaVersion') != 2:
        raise ValueError('Unsupported student record; original preserved')
    for key, value in prototype.items():
        if key not in data or (value is not None and type(data[key]) is not type(value)):
            raise ValueError('Invalid student field: ' + key)
    if data['current'] is not None and not isinstance(data['current'], dict):
        raise ValueError('Invalid current lesson')
    return data


class School:
    def __init__(self, home, session):
        self.home = Path(home).expanduser().resolve()
        self.session = session
        self.state = self.home / 'state'
        self.state.mkdir(parents=True, exist_ok=True)
        self.target = self.state / 'school.json'

    def read(self):
        if self.target.exists() and self.target.stat().st_size > 20_000_000:
            raise ValueError('Student record too large; export and inspect it')
        data = validate(read_json(self.target, initial()))
        return data

    def curriculum(self):
        key = hashlib.sha256(self.session.encode()).hexdigest()
        pin = read_json(self.home / 'cache/sessions' / (key + '.json'), {})
        if not pin:
            raise ValueError('Run launch.py start --session with this session ID first')
        version(pin['version'])
        root = self.home / 'courses' / pin['version']
        if not (root / 'teaching/lesson-index.json').is_file():
            raise ValueError('This course version predates Local School; update courses in a new session')
        return root, read_json(root / 'teaching/lesson-index.json')

    def lesson(self, lid):
        root, index = self.curriculum()
        item = next((x for x in index if x['id'] == lid), None)
        if item is None:
            raise ValueError('Unknown lesson ID')
        # Generated filenames, not user paths.
        base = root / 'teaching/lessons' / ('chapter%02d' % item['chapterId']) / lid
        if root.resolve() not in base.resolve().parents:
            raise ValueError('Invalid lesson path')
        return root, item, base

    def update(self, action):
        lock = self.state / '.write.lock'
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.close(fd)
            data = self.read()
            result = action(data)
            validate(data)
            if self.target.exists():
                backup = self.home / 'backups/school' / (str(time.time_ns()) + '.json')
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(self.target.read_bytes())
            data['lastLearningAt'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            atomic_json(self.target, data)
            return result
        finally:
            lock.unlink(missing_ok=True)

    def start(self):
        root, index = self.curriculum()
        data = self.read()
        legacy = {kind: read_json(self.state / (kind+'.json'), {}) for kind in ('progress','mastery','mistakes','notes')}
        return dict(status='returning' if data['profile'] else 'onboarding', state=data,
                    legacy=legacy, migrations=read_json(root/'migrations.json'), version=root.name,
                    pedagogy=str(root/'teaching/pedagogy.md'), routes=read_json(root/'teaching/routes.json'),
                    lessonCount=len(index))

    def enroll(self, route, level):
        if route not in ROUTES or level not in LEVELS:
            raise ValueError('Unknown route or difficulty')
        def action(data):
            data['profile'].setdefault('enrolledAt', time.time())
            data['profile'].update(route=route, difficulty=level)
            return data['profile']
        return self.update(action)

    def choose(self, lid):
        root, item, base = self.lesson(lid)
        def action(data):
            if data['current'] and data['current'].get('lessonId') == lid and data['current'].get('version') == root.name:
                current = data['current']
            else:
                current = dict(lessonId=lid, version=root.name, phase='explain', position='')
            data['current'] = current
            return dict(current=current, lecture=str(base.with_suffix('.md')),
                        unmetPrerequisites=[x for x in item['prerequisites'] if x not in data['completed']],
                        message='前置知识仅提醒，可以按目标选择课程。')
        return self.update(action)

    def question(self, lid, qid):
        _, _, base = self.lesson(lid)
        bank = read_json(base.with_suffix('.assessment.json'))
        q = next((x for x in bank['questions'] + bank['test'] if x['id'] == qid), None)
        if q is None:
            raise ValueError('Unknown question ID')
        return q

    def answer(self, lid, qid, answer):
        q = self.question(lid, qid)
        if not isinstance(answer, list) or not all(isinstance(x, str) for x in answer):
            raise ValueError('Answers must be a JSON string array')
        expected = q['answer']
        if q['type'] == 'multiple':
            correct = len(answer) == len(set(answer)) and set(answer) == set(expected)
        elif q['type'] == 'fill':
            correct = len(answer) == 1 and answer[0].strip().casefold() in [x.strip().casefold() for x in expected]
        else:
            correct = answer == expected
        def action(data):
            evidence = dict(lessonId=lid, questionId=qid, answer=answer, correct=correct,
                            version=self.curriculum()[0].name, timestamp=time.time())
            data['attempts'].append(evidence)
            if not correct:
                data['mistakes'].setdefault(qid, []).append(evidence)
            latest = {x['questionId']: x for x in data['attempts'] if x['lessonId'] == lid}
            data['mastery'][lid] = dict(correct=sum(x['correct'] for x in latest.values()), attempted=len(latest), basis='latest-quiz-answers')
            data['weakPoints'] = sorted({x['lessonId'] for x in data['attempts'] if not x['correct'] and not next(y for y in reversed(data['attempts']) if y['questionId'] == x['questionId'])['correct']})
            return dict(correct=correct, explanation=q['explanation'], expected=expected, mastery=data['mastery'][lid])
        return self.update(action)

    def record(self, kind, lid, text):
        self.lesson(lid)
        if not text or len(text) > 20000:
            raise ValueError('Record text must contain 1–20000 characters')
        def action(data):
            if kind == 'note':
                data['notes'].setdefault(lid, []).append(text)
            elif kind == 'bookmark':
                if lid not in data['bookmarks']: data['bookmarks'].append(lid)
            elif kind == 'skip':
                if lid not in data['skipped']: data['skipped'].append(lid)
            elif kind == 'phase':
                if not data['current'] or data['current']['lessonId'] != lid:
                    raise ValueError('Choose the lesson first')
                phase, _, position = text.partition(':')
                if phase not in PHASES: raise ValueError('Unknown teaching phase')
                data['current'].update(phase=phase, position=position)
            return dict(saved=kind, lessonId=lid)
        return self.update(action)

    def finish(self, lid):
        root, _, base = self.lesson(lid)
        bank = read_json(base.with_suffix('.assessment.json'))
        def action(data):
            latest = {x['questionId']: x for x in data['attempts'] if x['lessonId']==lid and x['version']==root.name}
            required = [q['id'] for q in bank['questions'] + bank['test']]
            if not all(q in latest for q in required):
                raise ValueError('Complete classroom and post-lesson questions first')
            score = sum(latest[q]['correct'] for q in required)/len(required)
            if score < .7: raise ValueError('Review weak points before completing this lesson (70% required)')
            if not data['labs'].get(lid, {}).get('reviewed'):
                raise ValueError('Practice evidence must be reviewed first; self-report is not execution evidence')
            data['completed'][lid] = dict(version=root.name, score=score, timestamp=time.time())
            route = read_json(root/'teaching/routes.json')[data['profile'].get('route','full')]['lessons']
            data['recommendation'] = next((x for x in route if x not in data['completed'] and x not in data['skipped']), None)
            return dict(completed=lid, score=score, next=data['recommendation'])
        return self.update(action)

    def lab(self, lid, review=None):
        _, item, base = self.lesson(lid)
        root = Path.home() / 'AI-Academy-Labs'
        folder = root / ('chapter%02d' % item['chapterId']) / lid
        if root.resolve() not in folder.resolve().parents or root.is_symlink():
            raise ValueError('Lab path escapes the lab directory')
        folder.mkdir(parents=True, exist_ok=True)
        task = folder/'TASK.md'
        if not task.exists():
            with task.open('x', encoding='utf-8') as stream:
                stream.write(base.with_suffix('.md').read_text(encoding='utf-8'))
        # Never overwrite a student's existing file.
        if lid == '06-01' and not (folder/'hello.py').exists():
            with (folder/'hello.py').open('x', encoding='utf-8') as stream:
                stream.write('# 请补充一行代码，让终端输出：你好\n')
        def action(data):
            record = data['labs'].setdefault(lid, dict(path=str(folder), reviewed=False))
            if review:
                if len(review) > 20000: raise ValueError('Evidence too long')
                record.update(reviewed=True, evidence=review, evidenceType='tutor-reviewed', timestamp=time.time())
            return record
        return self.update(action)

    def export(self, destination):
        files = {p.name: json.loads(p.read_text(encoding='utf-8')) for p in self.state.glob('*.json')}
        payload = json.dumps(files, ensure_ascii=False, sort_keys=True).encode()
        envelope = dict(format='ai-academy-state-v2', files=files, sha256=hashlib.sha256(payload).hexdigest())
        with Path(destination).open('x', encoding='utf-8') as stream:
            json.dump(envelope, stream, ensure_ascii=False, indent=2)
        return dict(exported=str(destination))

    def restore(self, source, confirm=False):
        if not confirm: raise ValueError('Import replaces records; explicit confirmation required')
        source = Path(source)
        if source.stat().st_size > 20_000_000: raise ValueError('Backup too large')
        envelope = read_json(source)
        files = envelope['files']
        allowed = {'school.json','progress.json','mastery.json','mistakes.json','notes.json'}
        payload = json.dumps(files, ensure_ascii=False, sort_keys=True).encode()
        if envelope.get('format') != 'ai-academy-state-v2' or hashlib.sha256(payload).hexdigest()!=envelope.get('sha256') or not set(files)<=allowed:
            raise ValueError('Invalid backup')
        validate(files.get('school.json', initial()))
        if any(not isinstance(v, dict) for v in files.values()): raise ValueError('Invalid backup records')
        lock = self.state / '.write.lock'
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        previous = {name: (self.state/name).read_bytes() if (self.state/name).exists() else None for name in files}
        try:
            os.close(fd)
            backup = self.home/'backups'/('before-import-'+str(time.time_ns())+'.json')
            backup.parent.mkdir(parents=True, exist_ok=True)
            self.export(backup)
            try:
                for name, value in files.items(): atomic_json(self.state/name, value)
            except Exception:
                for name, body in previous.items():
                    if body is None: (self.state/name).unlink(missing_ok=True)
                    else: (self.state/name).write_bytes(body)
                raise
            return dict(restored=list(files), backup=str(backup))
        finally:
            lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description='AI Academy 本地课堂')
    parser.add_argument('command', choices=['start','enroll','choose','question','answer','phase','note','bookmark','skip','finish','lab-create','lab-review','read','export','import'])
    parser.add_argument('--home', type=Path, default=Path.home()/'.ai-academy')
    parser.add_argument('--session', default='maintenance')
    parser.add_argument('--lesson'); parser.add_argument('--question')
    parser.add_argument('--route', choices=ROUTES, default='full')
    parser.add_argument('--level', choices=LEVELS, default='beginner')
    parser.add_argument('--text'); parser.add_argument('--answer-json')
    parser.add_argument('--file', type=Path); parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    school = School(args.home, args.session)
    try:
        if args.command == 'start': result = school.start()
        elif args.command == 'read': result = school.read()
        elif args.command == 'enroll': result = school.enroll(args.route, args.level)
        elif args.command == 'choose': result = school.choose(args.lesson)
        elif args.command == 'question': result = {k:v for k,v in school.question(args.lesson,args.question).items() if k not in ('answer','explanation')}
        elif args.command == 'answer': result = school.answer(args.lesson,args.question,json.loads(args.answer_json))
        elif args.command == 'finish': result = school.finish(args.lesson)
        elif args.command == 'lab-create': result = school.lab(args.lesson)
        elif args.command == 'lab-review':
            if not args.text: raise ValueError('Include actual observed output or inspected work, never inferred success')
            result = school.lab(args.lesson, args.text)
        elif args.command == 'export': result = school.export(args.file)
        elif args.command == 'import': result = school.restore(args.file,args.confirm)
        else: result = school.record(args.command,args.lesson,args.text or args.command)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, str(exc)+'\n')


if __name__ == '__main__': main()
