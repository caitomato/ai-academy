# coding: utf-8
"""Build the original, self-contained project used by lesson 02-04."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
chapter = json.loads((ROOT / 'src/data/curriculum/chapter02.json').read_text(encoding='utf-8'))
lesson = next(item for item in chapter['lessons'] if item['id'] == '02-04')
files = {item['name'].strip(): item['content'] for item in lesson['experience']['files'] if item.get('content')}
files['src/main.js'] = files.pop('main.js')
files['index.html'] = '<!doctype html>\n<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>学习计时器 · 启动练习</title><body><h1>学习计时器</h1><p>此练习只验证按钮状态切换，尚未实现实际计时。</p>' + files['index.html'] + '</body></html>\n'
files['README.md'] = '# 学习计时器 · 启动练习\n\n原创最小网页项目，仅实现按钮状态切换，不是真实计时应用。\n\n本项目要求受支持的 Node >=22.12.0，使用 npm。解压后进入含 package.json 的 study-timer 目录，先检查版本、配置和依赖，然后 npm install，再 npm run dev。打开终端给出的本地地址，点击按钮确认变为“计时中”，完成后 Ctrl+C。npm run build 验证生产构建。安装会从 npm 注册表获取依赖，并可能执行包脚本。\n\npackage-lock.json 和 node_modules 在安装后生成。不要把两者与手写源文件混淆。\n'
target = ROOT / 'public/practice-kit/study-timer.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, content in sorted(files.items()):
        info = zipfile.ZipInfo('study-timer/' + name, (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content.encode('utf-8'))
print(target)
central = ROOT / 'content/labs/study-timer.zip'
central.parent.mkdir(parents=True, exist_ok=True)
central.write_bytes(target.read_bytes())
