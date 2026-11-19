import release from "../data/published-release.json";

export function CourseUpdates() {
  return <section className="panel" style={{ margin: "2rem 0", padding: "1.5rem" }} aria-label="课程更新">
    <h2>最新课程版本</h2>
    <p>{release.version ? `稳定版 ${release.version} · ${release.releaseDate}` : "首个中央课程版本尚未正式发布"}</p>
    <ul>{release.changelog.map((line) => <li key={line}>{line}</li>)}</ul>
    {([['新增课程', release.added], ['修改课程', release.modified], ['修复内容', release.fixed]] as const).map(([label, items]) => items.length > 0 && <p key={label}><strong>{label}：</strong>{items.join('；')}</p>)}
    <details><summary>本地课程如何更新？</summary>
      <p>第一次安装轻量 Bootstrap 后，AI Academy 在新学习会话开始时自动检查课程版本，默认六小时缓存，无需反复安装或设置导师。重大教学逻辑变化会先征求确认，正在学习的课程不会中途切换。</p>
      <p>手动检查：在 Codex 或 Claude Code 中输入「检查 AI Academy 课程更新」。离线时继续使用已缓存版本；首次使用需要联网。更新只更换课程，学习进度、错题和笔记保存在你的电脑上。</p>
      <p><a href="./downloads/ai-academy-bootstrap.zip" download>下载本地 Skill 教学版</a> · 解压后使用 Python 3.11+ 运行 <code>python install.py --host codex</code>，Claude Code 用户将 codex 改为 claude。开启新会话，输入「带我学习 AI Academy」。</p>
      <p>可选择全栈、Agent 开发、AI 编程或 AI 创作路线，默认从零基础讲起。导师按课加载教材，陪你答题、在本地运行练习，并保存笔记、错题和学习位置。<a href="https://github.com/caitomato/ai-academy/blob/main/LOCAL-SCHOOL.md">安装、备份与故障排查</a></p>
      <p>安装器、Bootstrap 核心和课程分别版本化。核心升级使用安装目录中的 <code>python install.py --upgrade --host codex</code>；失败仍保留旧核心。课程包和完整性清单可在 <a href="https://github.com/caitomato/ai-academy/releases">正式版本记录</a> 中查看。</p>
    </details>
  </section>;
}
