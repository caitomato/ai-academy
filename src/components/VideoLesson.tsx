import { useState } from "react";
import videos from "../data/video-index.json";

const commands = ["node --version", "npm --version", "node", "let a = 10", "let b = 20", "console.log(a + b)", ".exit"];
const outputs = ["v24.x.x（示意版本）", "11.x.x（示意版本）", "Welcome to Node.js. 提示符变为 >", "undefined", "undefined", "30\nundefined", "已返回 PowerShell"];
export function terminalAnswer(step: number, input: string) {
  const normalized = input.trim().replace(/\s+/g, "").replace(/;$/, "");
  return normalized === commands[step]?.replace(/\s+/g, "");
}

export function VideoLesson({ lessonId, completed, onComplete }: { lessonId: string; completed: boolean; onComplete: () => void }) {
  const video = videos.find((item) => item.lessonId === lessonId && item.sample);
  const [step, setStep] = useState(0);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  if (!video) return null;
  return <section id="video-knowledge" className="reading video-lesson">
    <span className="eyebrow">视频融合 · 样板课程</span>
    <h2>从“装好了”到“确实能运行”</h2>
    <p className="muted">{video.videoTitle} · 03:22 · 常用工具 / Node.js 与 npm</p>
    <p>学习目标：区分运行时与包管理器，亲手验证环境，识别终端和 JavaScript 交互环境，读懂一次安装失败。</p>
    <div className="source-note"><strong>来源与核对范围</strong><p>PDF 第 36–39 页提供基础主题；视频文稿和 12 页在线课件补充了 REPL 运算、npm 命令和错误示例。下面的讲解、示意与练习均为原创改写。尚未完成连续视频画面复核，不能视为完整逐帧分析。</p><p>原视频未配置公开传播许可，因此这里不上传原片、完整文稿或讲师截图。时间戳尚待核对，不提供虚构的跳转位置。资料版本不明，界面与命令以当前官方文档为准。</p></div>
    <h3>视频知识点</h3>
    {video.keyPoints.map((point) => <p key={point}>{point}</p>)}
    <h3 id="video-frames">重点画面 · 原创重绘</h3>
    <p className="muted">按已核对课件还原教学状态；不是原视频截图，无人物头像。</p>
    <div className="video-visuals">
      <figure><div className="runtime-map"><span>你的 JavaScript</span><b>↓</b><span>Node.js 运行</span><b>↓</b><span>终端输出结果</span></div><figcaption>课件第 4 页：进入 Node 后，提示符由 PS…&gt; 变为 &gt;。此时输入 JavaScript。</figcaption></figure>
      <figure><pre><code>{"> let a = 10\nundefined\n> let b = 20\nundefined\n> console.log(a + b)\n30\nundefined"}</code></pre><figcaption>原创补全演示：30 是打印结果；随后出现 undefined，是 console.log 的返回值，不是运行失败。</figcaption></figure>
      <figure><pre><code>{"npm error code E404\nnpm error 404 Not Found"}</code></pre><figcaption>课件第 7 页的错误类型：注册表没有找到请求的包。核对包名、官方安装说明和注册表地址，不能仅凭此认定是重复安装。</figcaption></figure>
    </div>
    <h3 id="video-practical">实操教程 · 先在模拟终端试一次</h3>
    {completed && <p className="source-note">✓ 已记录模拟实操完成。可再次练习；这条记录不代表本机环境已通过验收。</p>}
    <p>本练习不执行电脑命令，也不安装软件。先输入 <code>{commands[step] || "练习已完成"}</code>。版本号为示意，真实电脑可显示不同的受支持版本。</p>
    <div className="terminal-simulator">
      <pre aria-label="模拟终端输出">{commands.slice(0, step).map((command, i) => `${i >= 3 && i <= 6 ? ">" : "PS>"} ${command}\n${outputs[i]}`).join("\n") || "模拟 PowerShell · 等待输入"}</pre>
      {step < commands.length ? <form onSubmit={(event) => { event.preventDefault(); if (terminalAnswer(step, input)) { setStep(step + 1); setInput(""); setError(""); } else setError("请对照本步命令检查拼写；此模拟器仅识别课程中的七条命令。"); }}>
        <label htmlFor="node-command">第 {step + 1} / 7 步 · 输入命令</label>
        <div className="terminal-entry"><input id="node-command" value={input} onChange={(event) => setInput(event.target.value)} autoComplete="off" spellCheck={false} /><button type="submit">运行模拟</button></div>
        <p role="status">{error}</p>
      </form> : <><p role="status">练习完成：你已验证版本、进入 REPL、得到 30，并退出到终端。</p><button onClick={onComplete} disabled={completed}>{completed ? "模拟实操已记录" : "记录模拟实操完成"}</button></>}
      <button className="sim-reset" onClick={() => { setStep(0); setInput(""); setError(""); }}>重新练习</button>
    </div>
    <h3>在自己电脑上复现</h3>
    <ol>{video.practicalSteps.map((item) => <li key={item}>{item}</li>)}</ol>
    <h3>来源差异与排障</h3>
    <p>视频把 npm 比作应用商店，便于入门；准确说它是包管理器。全局安装使用 -g，但项目依赖通常按项目说明安装，不要把所有命令都加上 -g。视频中的错误归因与画面不完全一致，应优先阅读实际错误。</p>
    <p>如果提示“无法识别 node”，检查是否安装和 PATH 是否生效，重新打开终端；不要继续输入 JavaScript。如果 npm.ps1 被执行策略阻止，可在 Windows 尝试 npm.cmd --version 并核对官方说明。此处不要求修改系统策略。</p>
    <p>额外补充：npx、依赖和锁文件属于本课文字拓展，不是这段视频已经完整演示的内容。安装、卸载和更新会改变环境，本节只要求验证与运算，不要求复现视频的失败安装。</p>
    <p><strong>应用任务：</strong>给同伴写一张环境验收卡，包含 Node/npm 版本、提示符切换、运算结果和退出方式。随后完成下方 3 道互动题与 4 道测试。</p>
    <details><summary>查看全部视频的资料处理清单（35 个）</summary>
      <p>当前目录 28 个，归档 7 个。已知 32 个时长共 8 小时 7 分 18 秒，另 3 个待核对。全部文稿已阅读；本次仅 Node 样板完成 12 页课件核对和课程融合，连续画面及时间戳仍待复核。未完成的项目不计为质量检查通过。</p>
      <ul>{videos.map((item) => <li key={item.videoId}><strong>{item.fileName}</strong><br />主课 {item.lessonId} · {item.duration === null ? "时长待核对" : `${Math.floor(item.duration / 60)}:${String(item.duration % 60).padStart(2, "0")}`} · {item.archive ? "归档" : "当前教程"} · {item.sample ? "样板已生成，连续画面待复核" : "文稿已读，画面分析待处理"}</li>)}</ul>
    </details>
  </section>;
}
