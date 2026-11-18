import { useState } from "react";
import type { Lesson } from "../types";

export function PracticeLab({ lab }: { lab: NonNullable<Lesson["lab"]> }) {
  const [copyStatus, setCopyStatus] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(lab.prompt);
      setCopyStatus("已复制，可以粘贴到自己的练习工具中。");
    } catch {
      setCopyStatus("请选中下面的任务文字，手动复制。");
    }
  }
  return (
    <div className="practice-lab">
      <span className="eyebrow">跟着做 · 留下一份可检查的成果</span>
      <h3>{lab.title}</h3>
      <p>{lab.setup}</p>
      {lab.resources && <>
        <h4>先准备材料与参考</h4>
        <ul>{lab.resources.map((item) => <li key={item.href}>
          <a href={item.href} download={item.download || undefined}
            target={item.download ? undefined : "_blank"}
            rel={item.download ? undefined : "noreferrer"}>{item.title}</a>
        </li>)}</ul>
      </>}
      <div className="lab-prompt">
        <div className="lab-prompt-header">
          <strong>任务卡</strong>
          <button className="secondary" onClick={copy}>复制任务</button>
        </div>
        <pre>{lab.prompt}</pre>
        <p role="status" className="muted">{copyStatus || "可以在自己的工具中实践，也可以先在下方笔记里写出方案。"}</p>
      </div>
      <ol className="lab-walkthrough">
        {lab.walkthrough.map((step) => (
          <li key={step.action}>
            <strong>{step.action}</strong>
            <p>{step.expected}</p>
            {step.code && <pre><code>{step.code}</code></pre>}
          </li>
        ))}
      </ol>
      <h4>怎样算做完了</h4>
      <ul>{lab.checks.map((check) => <li key={check}>{check}</li>)}</ul>
      <h4>遇到问题，先看这里</h4>
      {lab.troubleshooting.map((item) => (
        <details key={item.symptom}>
          <summary>{item.symptom}</summary>
          <p>{item.remedy}</p>
        </details>
      ))}
    </div>
  );
}
