# coding: utf-8
"""Audit all chapters and the shipped bundle; private report stays ignored."""
from pathlib import Path
from collections import Counter
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
lessons=[l for p in sorted((ROOT/'src/data/curriculum').glob('*.json')) for l in json.loads(p.read_text(encoding='utf-8'))['lessons']]
questions=[q for l in lessons for q in l['questions']+l['test']]
problems=[]
for l in lessons:
    raw=json.dumps(l,ensure_ascii=False)
    for pattern in [r'视频融合',r'视频知识点',r'\.mp4',r'课件第\s*\d',r'逐帧核对',r'第一个关键词']:
        if re.search(pattern,raw):problems.append(l['id']+': '+pattern)
    for q in l['questions']+l['test']:
        if any(a and a in q['hint'] for a in q['answer']):problems.append(q['id']+': answer repeated in hint')
        if q['type']!='fill' and not set(q['answer'])<=set(q['options']):problems.append(q['id']+': invalid answer')
        if len(q['options'])!=len(set(q['options'])):problems.append(q['id']+': duplicate choices')
examples=Counter(l['example'] for l in lessons)
for text,count in examples.items():
    if count>1:problems.append('Duplicate case: '+text)
# Compare all original persisted IDs against the release preceding this refactor.
baseline=[]
for n in range(1,10):
    result=subprocess.run(['git','show',f'8ab85b8:src/data/curriculum/chapter{n:02}.json'],cwd=ROOT,capture_output=True,encoding='utf-8',check=True)
    baseline+=json.loads(result.stdout)['lessons']
old_lids={l['id'] for l in baseline};new_lids={l['id'] for l in lessons}
old_qids={q['id'] for l in baseline for q in l['questions']+l['test']}
if old_lids!=new_lids or old_qids!={q['id'] for q in questions}:problems.append('Persisted IDs changed')
bundle=''.join(p.read_text(encoding='utf-8') for p in (ROOT/'dist').rglob('*.js'))
for term in ['视频融合','视频知识点','videoId','2-常用工具-3-Node.mp4','归档（内容可忽略','课件第 7 页']:
    if term in bundle:problems.append('Bundle contains source production data: '+term)
report=ROOT/'materials/reports/course-quality-v2.md';report.parent.mkdir(parents=True,exist_ok=True)
report.write_text('''# V2 课程质量检查\n\n范围：九章 90 节、630 题、编译后的浏览器脚本。\n\n修复：\n- 删除公开视频索引及专用展示组件；内部源目录保存在忽略目录。\n- 02-04 改为独立项目叙事，三种实验、八步启动、五种排障、七道知识题全部重写。\n- 其余 89 节逐课增加概念辨析或应用问题，替换按术语位置填空（Token 保留有知识意义的计费单元回忆题），题号不变。\n- 去除重复案例段与重复误区段，缩短重复答案讲解；整理导入、目标、总结及末尾参考区。\n- 02-04 的 DOM 与 Node 环境、锁文件、开发依赖、engines 的非强制语义、安装副作用、本地与部署边界均单独解释。\n\n检查结果：\n'''+('\n'.join('- '+p for p in problems) if problems else '- 自动检查未发现上述禁用痕迹、答案越界、选项重复、逐字重复案例或直接答案提示。\n- 90 个课号、630 个题号与改版前完全一致。')+'''\n\n人工检查边界：全站目录、讲解/题干模式、误区和新辨析题已逐项扫描；没有重新把全部外部工具实机安装和测试，没有宣称完成全量原资料版权鉴定。公开素材为已有原创练习与代码图示，未加入来源截图。其余课程仍存在共享的基础题型与通用页面骨架；它们并不等于已完成 Node 级别的专用实验。按验收顺序，后续专用可视化须各课设计并验证，不能自动套同一个模拟器。\n''',encoding='utf-8')
print(f'{len(lessons)} lessons / {len(questions)} questions; {len(problems)} audit failures; private report: {report}')
for p in problems:print(p)
raise SystemExit(bool(problems))
