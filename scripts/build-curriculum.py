"""Compile original editorial seeds into independently maintainable chapter JSON files."""
from pathlib import Path
import json
from video_enrichment import enrich
from node_course import apply_sample
from course_quality import apply_quality

ROOT = Path(__file__).resolve().parents[1]
chapters = []
for line in (ROOT / 'scripts/course-seeds.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    if line.startswith('# '):
        n, title, desc = line[2:].split('|')
        chapters.append(dict(id=int(n), title=title, description=desc, lessons=[]))
        continue
    title, pages, core, example, mistake, task, terms, steps = line.split('|')
    chapter = chapters[-1]
    lid = f"{chapter['id']:02}-{len(chapter['lessons'])+1:02}"
    chapter['lessons'].append(dict(id=lid, chapterId=chapter['id'], title=title, pages=pages,
        minutes=12 if chapter['id'] < 6 else 15,
        objectives=[f"用自己的话解释{terms.split(',')[0]}", '能按照案例完成一个小练习', '识别常见误区并说明原因'],
        sections=[dict(title='先建立直觉', text=core), dict(title='把概念放进场景', text=example), dict(title='辨清边界', text='容易混淆的说法：“'+mistake+'” 这个说法不成立。'+core)],
        example=example, task=task, steps=steps.split('>'), terms=terms.split(','), misconception=mistake,
        sourceNote='主题与页码来自本地学习资料；讲解、案例及题目为原创改写。软件版本、价格与安装方式需以使用时的官方文档为准。'))

codes = {
'06-01': ('print("你好")', '你好', ['hello.py', '没有输出'], 'print 会把括号中的字符串输出到终端，文件名本身不会成为输出。'),
'06-03': ('age = "18"\nprint(int(age) + 1)', '19', ['181', '18'], 'int 把数字字符串转换为整数，因此执行数值加法，而非字符串拼接。'),
'06-04': ('print(17 // 5, 17 % 5)', '3 2', ['3.4 2', '2 3'], '// 得到整除结果 3，% 得到余数 2，满足 17 = 3 × 5 + 2。'),
'06-05': ('tasks = ["阅读", "练习"]\ntasks.append("复习")\nprint(len(tasks), tasks[0])', '3 阅读', ['2 阅读', '3 练习'], 'append 增加一个元素，长度变为 3；索引 0 指第一个元素。'),
'06-06': ('point = (3, 5)\nprint(point[1])', '5', ['3', '运行报错'], '元组支持按索引读取；索引从 0 开始，所以索引 1 对应 5。'),
'06-07': ('record = {"minutes": 20}\nprint(record.get("score", 0))', '0', ['20', '运行报错'], 'score 不存在，get 返回指定的默认值 0，而不是读取 minutes。'),
'06-08': ('score = 85\nif score >= 90:\n    print("A")\nelif score >= 80:\n    print("B")\nelse:\n    print("C")', 'B', ['A', 'A B'], '第一项条件不满足，第二项满足，所以只执行第二个分支。'),
'06-09': ('total = 0\nfor n in [10, 20, 30]:\n    total += n\nprint(total)', '60', ['30', '0'], '循环依次累加 10、20、30，最后才输出总和。'),
'06-10': ('def add(a, b):\n    return a + b\nprint(add(2, 3))', '5', ['None', '2 3'], '调用函数后 return 把和交回调用者，print 显示这个返回值。'),
'06-11': ('import math\nprint(math.isqrt(25))', '5', ['25', '625'], 'math.isqrt 返回非负整数的整数平方根；25 的平方根为 5。'),
'06-14': ('name: str = "学习者"\nprint(type(name).__name__)', 'str', ['int', 'None'], '值是字符串，type 返回实际运行时类型；注释用于说明预期类型。'),
}

for chapter in chapters:
    lessons = chapter['lessons']
    for i, lesson in enumerate(lessons):
        lid = lesson['id']; core = lesson['sections'][0]['text']; example = lesson['example']; mistake = lesson['misconception']
        first = core.split('。')[0]+'。'
        distractor = lessons[(i+1) % len(lessons)]['sections'][0]['text'].split('。')[0]+'。'
        def question(suffix, kind, prompt, options, answer, explanation, hint, **extra):
            return dict(id=lid+'-'+suffix,lessonId=lid,type=kind,prompt=prompt,options=options,answer=answer,explanation=explanation,hint=hint,**extra)
        options = [first, mistake, '不需要区分概念，也不必检查实际结果。']
        # Rotate correct choices so their positions are not predictable.
        offset = i % 3; options = options[offset:]+options[:offset]
        lesson['questions'] = [
            question('p1','single',f"关于{lesson['title']}，哪项理解正确？",options,[first],f'正确理解：{core} 错误选项忽略了本节的边界或验证条件；尤其要避免“{mistake}”这一误区。','先回看“先建立直觉”，区分能力与保证。'),
            question('p2','boolean',f'判断这句话是否成立：{mistake}',['成立','不成立'],['不成立'],f'这句话不成立。{core} 例如：{example}','留意“一定”“任何”“不需要”等过度推断。'),
            question('p3','fill',f"填写术语：本节第一个关键词是“____”（提示：{first}）",[],[lesson['terms'][0]],f"答案为 {lesson['terms'][0]}。{first} 注意术语命名不能代替对实际用途的理解。",'在本节“关键术语”列表中找到第一个词。')]
        scenario = example.split('。')[0]+'。'
        test = [
            question('t1','single',f'哪一个场景最直接体现本节“{lesson["title"]}”的知识？',[scenario,lessons[(i+1)%len(lessons)]['example'].split('。')[0]+'。',lessons[(i+2)%len(lessons)]['example'].split('。')[0]+'。'],[scenario],f'{example} 其余场景属于相邻课程，未直接展示本节核心机制。','把场景中的动作与本节概念对应。'),
            question('t2','order','把本节建议的实践流程排列为合理顺序。',list(reversed(lesson['steps'])),lesson['steps'],'先后顺序为：'+' → '.join(lesson['steps'])+'。前一步提供后一步需要的输入或验证依据，直接跳到结果会遗漏中间检查。','先确认输入与准备，再执行，最后检查结果。'),
            question('t3','multiple','选择所有符合本节内容的陈述（多选）。',[mistake,first,example],[first,example],f'概念陈述与案例都成立：{core} 案例：{example} 不能选择误区“{mistake}”。','概念与实际案例可以同时正确；排除过度保证。'),
            question('t4','single','复盘时，哪一项值得保留为本节的关键认识？',[mistake,distractor,first],[first],f'{core} “{mistake}”不成立；另一项属于相邻主题，不能替代本节核心认识。','选择与本节目标直接对应的结论。')]
        for j,q in enumerate(test):
            if q['type']=='single':
                off=(i+j+1)%3; q['options']=q['options'][off:]+q['options'][:off]
        if lid in codes:
            code,answer,wrong,explanation=codes[lid]
            lesson['code']=code
            test[0]=question('t1','code','阅读下面的 Python 代码，选择输出结果。',[wrong[0],answer,wrong[1]],[answer],explanation,'按行模拟执行，留意类型和索引。',code=code)
        lesson['test']=test
        enrich(lesson)
        apply_sample(lesson)
        apply_quality(lesson)
    # Authoring seeds export to the central release source and its web projection.
    for directory in ('content/chapters', 'src/data/curriculum'):
        (ROOT/f"{directory}/chapter{chapter['id']:02}.json").write_text(json.dumps(chapter,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Compiled {len(chapters)} chapters, {sum(len(c['lessons']) for c in chapters)} lessons")
