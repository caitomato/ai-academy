"""Generate progressive lesson files and reference indexes from central JSON."""
import json


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def generate(chapters):
    files, index, gaps = {}, [], []
    for chapter in chapters:
        previous = None
        for lesson in chapter['lessons']:
            lid = lesson['id']
            base = f'teaching/lessons/chapter{chapter["id"]:02}/{lid}'
            dependencies = [previous] if previous else ([] if chapter['id'] == 1 else ['01-05'] if chapter['id'] in (3,7) else ['01-01'])
            index.append(dict(id=lid, chapterId=chapter['id'], title=lesson['title'], objectives=lesson['objectives'], prerequisites=dependencies, lesson=base+'.md', data=base+'.json', assessment=base+'.assessment.json'))
            data = {k:v for k,v in lesson.items() if k not in ('questions','test')}
            files[base+'.json'] = encode(data)
            files[base+'.assessment.json'] = encode(dict(questions=lesson['questions'], test=lesson['test']))
            parts = [f'# {lid} · {lesson["title"]}', '## 今天要学什么', *['- '+x for x in lesson['objectives']], '## 为什么要学', lesson.get('introduction') or '这节课帮助你完成下面的实际任务：'+lesson['task'], '## 核心概念']
            for section in lesson['sections']:
                parts += ['### '+section['title'], section['text']]
            parts += ['## 原创案例', lesson['example'], '## 动手实践', lesson['task'], *[f'{i+1}. {step}' for i,step in enumerate(lesson['steps'])]]
            if lesson.get('code'): parts += ['```', lesson['code'], '```']
            if lesson.get('lab'):
                lab=lesson['lab'];parts += ['### '+lab['title'],lab['setup']]
                for step in lab['walkthrough']:
                    parts += ['- 操作：'+step['action'], '  预期：'+step['expected']]
                    if step.get('code'):parts += ['```',step['code'],'```']
                parts += ['### 验收',*['- '+x for x in lab['checks']]]
                for fault in lab['troubleshooting']:parts += ['- '+fault['symptom']+'：'+fault['remedy']]
            if lesson.get('experience'):
                parts += ['## 项目教程',json.dumps(lesson['experience'],ensure_ascii=False,indent=2)]
            parts += ['## 误区',lesson['misconception'],'## 小结',lesson.get('summary') or '完成后，请用自己的话解释关键概念，并用实际结果检查任务。','## 练习入口', '课堂练习和课后题由 school.py question / answer 按题加载。不要提前向学生展示答案。','## 来源',lesson.get('sourceNote','原创教学整理；参考说明见课程源。')]
            files[base+'.md']='\n\n'.join(parts).encode('utf-8')
            if not lesson.get('lab') and not lesson.get('experience'):
                gaps.append(dict(lessonId=lid,status='needs-dedicated-lab',reason='讲义、案例和七道题齐全；专用环境验证及项目验收仍需补充。当前可做概念练习或学习笔记，不冒充完整编程实验。'))
            previous=lid
    routes={
      'full':dict(title='AI 全栈学习路线',chapters=list(range(1,10))),
      'agent':dict(title='AI Agent 开发路线',chapters=[1,2,3,6,7,8]),
      'coding':dict(title='AI 编程路线',chapters=[1,2,4,6,7]),
      'creative':dict(title='AI 创作路线',chapters=[1,2,3,5,9])}
    for route in routes.values():route['lessons']=[l['id'] for n in route['chapters'] for l in index if l['chapterId']==n]
    files['teaching/lesson-index.json']=encode(index)
    files['teaching/routes.json']=encode(routes)
    files['teaching/coverage.json']=encode(dict(totalLessons=len(index),pendingLabs=gaps))
    files['teaching/lesson-index.md']=('\n'.join(['# 课程索引',*['- '+x['id']+' '+x['title']+' → '+x['lesson'] for x in index]])).encode('utf-8')
    files['teaching/curriculum-map.md']=('\n'.join(['# 学习路线',*['- '+x['title']+'：章节 '+', '.join(map(str,x['chapters'])) for x in routes.values()], '前置知识是提醒，不是强制锁课。跳课后不得把跳过的课记为完成。'])).encode('utf-8')
    return files
