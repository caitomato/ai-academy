import { useState } from "react";
import type { Lesson } from "../types";

export const commandTrials = [
  { command: "node --version", answer: "查看版本", explanation: "只查看 Node 版本，不执行项目。" },
  { command: "npm --version", answer: "查看版本", explanation: "查看 npm 版本，和 Node 版本号可以不同。" },
  { command: "node", answer: "进入交互环境", explanation: "打开 REPL，退出可输入 .exit。" },
  { command: "node hello.js", answer: "执行程序", explanation: "用 Node 执行独立脚本 hello.js。" },
];
export const startupCases = [
  { title: "运行时未就绪", output: "node : 无法将“node”项识别为命令", options: ["检查 Node 安装与 PATH，重开终端后验证版本", "先添加 dev 脚本", "修改页面颜色"], correct: 0, reason: "命令尚未找到，先解决运行时可用性；此时还没到项目脚本阶段。" },
  { title: "运行时版本不兼容", output: "本项目启动检查：需要 Node >=22.12.0\n当前：v18.20.0\n不满足要求，启动已停止（模拟项目检查）", options: ["忽略要求继续运行", "使用满足项目要求的受支持 Node 版本，再验证", "把 engines 删除"], correct: 1, reason: "版本要求来自本例项目。engines 在普通 npm 安装中不一定强制拦截；这里模拟项目自身的兼容性检查。" },
  { title: "清单没有找到", output: "npm error code ENOENT\nnpm error Could not read package.json", options: ["新建任意空清单掩盖错误", "清空 npm 缓存", "核对当前目录，进入含真实 package.json 的项目目录"], correct: 2, reason: "先核对位置和文件。缓存与启动脚本不能修复错误目录。" },
  { title: "本地工具没有准备好", output: "scripts.dev = vite\ndevDependencies 包含 vite\n当前项目未安装依赖\n'vite' is not recognized", options: ["检查项目可信来源后，在项目目录安装依赖", "全局安装每一个包", "重命名 src 目录"], correct: 0, reason: "本题已给出缺失证据：项目工具尚未安装。npm install 按清单准备本地依赖。" },
  { title: "脚本名不匹配", output: "npm error Missing script: dev\n当前 scripts: { start: 'vite' }", options: ["删除锁文件", "查看 npm run 与 README，确认后使用 npm run start", "重装操作系统"], correct: 1, reason: "此情境已有 start 脚本；先理解已有定义，不猜测所有项目都必须叫 dev。" },
  { title: "服务器就绪", output: "VITE ready\nLocal: http://localhost:5173/\n（浏览器内虚构输出，无服务器实际运行）", options: ["已公开上线，无需检查", "关闭终端再打开地址", "打开给出的本地地址并验证计时按钮"], correct: 2, reason: "服务器就绪后还要验收页面交互；终端通常需保持运行，完成后 Ctrl+C 停止。" },
];

export function NodeProject({ experience, completed, onComplete }: { experience: NonNullable<Lesson["experience"]>; completed: boolean; onComplete: () => void }) {
  const [file, setFile] = useState(0);
  const [field, setField] = useState(0);
  const [trial, setTrial] = useState(0);
  const [trialFeedback, setTrialFeedback] = useState("");
  const [mastered, setMastered] = useState<number[]>([]);
  const [scenario, setScenario] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [solved, setSolved] = useState<number[]>([]);
  const [inspected, setInspected] = useState<number[]>([]);
  const allDone = mastered.length === commandTrials.length && solved.length === startupCases.length && inspected.length === experience.fields.length;
  const selectedFile = experience.files[file];
  const current = startupCases[scenario];
  return <>
    <section id="project-structure" className="reading">
      <span className="eyebrow">项目地图</span><h2>先看懂你拿到的文件</h2>
      <p>这里是一份原创的学习计时器项目。点击目录条目，观察配置、源代码与安装产物的区别。示例版本是项目约定，不是安装推荐。</p>
      <div className="project-explorer">
        <div className="file-tree" role="group" aria-label="项目目录"><strong>{experience.projectName}/</strong>{experience.files.map((item, i) => <button key={item.name} aria-pressed={file === i} onClick={() => setFile(i)}><span aria-hidden="true">{item.name.endsWith("/") ? "▸" : "·"}</span>{item.name}</button>)}</div>
        <div className="file-detail" aria-live="polite"><h3>{selectedFile.name}</h3><p>{selectedFile.description}</p>{selectedFile.content && <pre><code>{selectedFile.content}</code></pre>}</div>
      </div>
    </section>
    <section id="project-workflow" className="reading">
      <span className="eyebrow">情景案例</span><h2>把学习计时器运行起来</h2>
      <p>下面是本机实践的八个检查点。命令仅作为说明，网站不会执行。操作你信任的项目；路径和版本要换成实际值。</p>
      <p><a className="text-link" href="./practice-kit/study-timer.zip" download>下载原创启动练习项目（ZIP）</a> · 解压后进入 study-timer 目录。它只实现按钮状态切换，用于验收启动链条，尚未实现真正计时。锁文件和依赖目录在首次安装后生成。</p>
      <ol className="workflow-rail">{experience.walkthrough.map((step, i) => <li key={step.title}><div className="rail-number">{String(i + 1).padStart(2, "0")}</div><div><h3>{step.title}</h3><p>{step.action}</p><pre><code>{step.command}</code></pre><dl><dt>为什么</dt><dd>{step.reason}</dd><dt>预期结果</dt><dd>{step.expected}</dd><dt>遇到错误</dt><dd>{step.recovery}</dd></dl></div></li>)}</ol>
    </section>
    <section id="experiments" className="reading experiments">
      <span className="eyebrow">交互实验室</span><h2>先预测，再排查</h2>
      <p>所有实验均在浏览器内模拟，不执行系统命令、不安装依赖、不启动真实服务器。实验结果单独记录，不代表本机验收。</p>
      {completed && <p className="experiment-complete">已记录本课实验完成，可随时重新尝试。</p>}
      <article className="experiment"><span className="experiment-label">A · 认识运行环境</span><h3>这条命令做什么？</h3><div className="experiment-select" role="group" aria-label="选择命令">{commandTrials.map((item, i) => <button key={item.command} aria-pressed={trial === i} onClick={() => { setTrial(i); setTrialFeedback(""); }}>{i + 1}{mastered.includes(i) ? " ✓" : ""}</button>)}</div><pre><code>{commandTrials[trial].command}</code></pre><div className="experiment-actions">{["查看版本", "进入交互环境", "执行程序"].map((answer) => <button key={answer} onClick={() => { const correct = answer === commandTrials[trial].answer; setTrialFeedback(correct ? `判断正确。${commandTrials[trial].explanation}` : "再试一次：观察命令参数，是查询、打开交互环境，还是指定了文件？"); if (correct) setMastered((previous) => [...new Set([...previous, trial])]); }}>{answer}</button>)}</div><p role="status">{trialFeedback}</p><p className="muted">已正确识别 {mastered.length} / 4 条命令</p></article>
      <article className="experiment"><span className="experiment-label">B · 理解项目配置</span><h3>清单里的三个区域</h3><p>选择一个字段阅读其值和含义，再记录该字段已理解。</p><div className="config-fields" role="group" aria-label="配置字段">{experience.fields.map((item, i) => <button key={item.name} aria-pressed={field === i} onClick={() => setField(i)}>{item.name}{inspected.includes(i) ? " ✓" : ""}</button>)}</div><pre><code>{experience.fields[field].content}</code></pre><p aria-live="polite">{experience.fields[field].explanation}</p><button onClick={() => setInspected((previous) => [...new Set([...previous, field])])} disabled={inspected.includes(field)}>{inspected.includes(field) ? "本字段已阅读" : "记录本字段已阅读"}</button></article>
      <article className="experiment"><span className="experiment-label">C · 模拟项目启动</span><h3>根据反馈选择下一步</h3><div className="scenario-picker" role="group" aria-label="故障情境">{startupCases.map((item, i) => <button key={item.title} aria-pressed={scenario === i} onClick={() => { setScenario(i); setFeedback(""); }}>{i + 1}. {item.title}{solved.includes(i) ? " ✓" : ""}</button>)}</div><pre aria-label="模拟启动反馈"><code>{current.output}</code></pre><div className="scenario-options">{current.options.map((option, i) => <button key={option} onClick={() => { const correct = i === current.correct; setFeedback(correct ? `处理正确。${current.reason}` : "这个操作没有对应当前错误的证据。先定位反馈发生在环境、目录、依赖还是脚本阶段，再选择。"); if (correct) setSolved((previous) => [...new Set([...previous, scenario])]); }}>{option}</button>)}</div><p role="status">{feedback}</p><p className="muted">已解决 {solved.length} / 6 个情境</p></article>
      <button className="primary" disabled={!allDone || completed} onClick={onComplete}>{completed ? "实验完成已保存" : allDone ? "保存本课实验完成记录" : "完成三个实验后可保存记录"}</button>
    </section>
    <section id="troubleshooting" className="reading"><span className="eyebrow">故障排除</span><h2>用证据缩小问题范围</h2><p>先保留原始错误，确认失败在哪一层，一次只修正一个有依据的问题，再重试验收。</p><div className="diagnosis-list">{experience.troubleshooting.map((item) => <details key={item.symptom}><summary>{item.symptom}</summary><p><strong>先查：</strong>{item.diagnosis}</p><p><strong>再做：</strong>{item.resolution}</p></details>)}</div></section>
  </>;
}
