"""Cross-curriculum editorial normalization; keeps persisted identities stable."""
from pathlib import Path
CHECKS = {}
for row in (Path(__file__).with_name('concept-checks.txt')).read_text(encoding='utf-8-sig').splitlines():
    key, prompt, correct, wrong, explanation = row.split('|')
    CHECKS[key] = (prompt, correct, wrong, explanation)

def apply_quality(lesson):
    lid = lesson['id']
    if lid == '02-04':
        return
    prompt, correct, wrong, explanation = CHECKS[lid]
    lesson['introduction'] = f"本节要完成的任务：{lesson['task']} 开始前，先想一想：{prompt}"
    lesson['objectives'] = [f"说明{lesson['terms'][0]}在任务中的作用", f"完成并检查成果：{lesson['task']}", '根据本节情境区分可验证结论与常见误判']
    # A repeated source paragraph is not a new concept.
    lesson['sections'] = [s for s in lesson['sections'] if s['title'] not in ('把概念放进场景', '辨清边界')]
    lesson['summary'] = f"本节的判断要点：{explanation} 实践后，用“{' → '.join(lesson['steps'])}”检查是否留下了可验收的结果。"
    lesson['sourceNote'] = '课程以独立任务、讲解与练习组织；研发参考《AI学习文档》及配套教学资料。工具版本、接口与服务限制以使用时官方说明为准。'
    q = lesson['questions'][2]
    q.update(type='single',prompt=prompt,options=[correct,wrong],answer=[correct],explanation=explanation,hint='比较两种处理方式的前提与后果，不用背术语顺序。')
    if sum(ord(x) for x in lid) % 2:
        q['options'].reverse()
    # Keep a genuinely useful terminology recall item for Token normalization.
    if lid == '01-02':
        q.update(type='fill',prompt='模型计费按文本处理单元统计，这个单元通常叫什么？（填写英文单数）',options=[],answer=['Token'],explanation='Token 是模型处理的文本单元，边界由分词器决定，不固定等于一个汉字。',hint='区分字符、字节与模型采用的分词单位。')
    # Explanations should explain the discrimination, not paste an entire lesson.
    for item in lesson['questions']:
        if item['id'].endswith('p1'):
            item['explanation'] = lesson['sections'][0]['text']
            item['hint'] = '判断陈述是否满足概念的适用条件。'
        elif item['id'].endswith('p2'):
            item['explanation'] = f"这里需要纠正的边界是：{lesson['sections'][0]['text']}"
            item['hint'] = '寻找绝对化断言遗漏的条件或反例。'
    for item in lesson['test']:
        if item['id'].endswith('t3') and item['prompt'] == '选择所有符合本节内容的陈述（多选）。':
            item['explanation'] = f"场景中的操作体现了概念，错误陈述忽略了条件：{lesson['misconception']}"
            item['hint'] = '逐项判断条件，不用按选项长度或位置猜测。'
        if item['id'].endswith('t4') and item['prompt'].startswith('复盘时'):
            item.update(prompt=f"准备提交本节实践成果：{lesson['task']} 哪项能帮助验收？",options=[f"按顺序检查：{' → '.join(lesson['steps'])}",'只保存一句“我已完成”，不保留过程或输出','只比较与任务无关的界面风格'],answer=[f"按顺序检查：{' → '.join(lesson['steps'])}"],explanation='验收必须覆盖任务的输入、操作与结果；主观声明和无关外观不能证明任务完成。',hint='把验收证据与本节任务逐项对应。')
        if item['hint'].startswith('在本节') or '第一个词' in item['hint']:
            item['hint'] = '根据场景的输入、操作与结果判断。'
