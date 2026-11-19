import { useState } from "react";
import type { Lesson } from "../types";

export function DecisionLab({ lab, completed, onComplete }: { lab: NonNullable<Lesson["decisionLab"]>; completed: boolean; onComplete: () => void }) {
  const [stage, setStage] = useState(0);
  const [choice, setChoice] = useState<number | null>(null);
  const [passed, setPassed] = useState<number[]>([]);
  const current = lab.stages[stage];
  return <section id="decision-lab" className="reading"><span className="eyebrow">交互实验 · 浏览器模拟</span><h2>{lab.title}</h2><p>{lab.introduction}</p>
    <div className="flex flex-wrap gap-2 my-4" role="group" aria-label="实验阶段">{lab.stages.map((item, i) => <button className="secondary" aria-pressed={stage === i} key={item.title} onClick={() => { setStage(i); setChoice(null); }}>{i + 1}. {item.title}{passed.includes(i) ? " ✓" : ""}</button>)}</div>
    <div className="decision-state"><h3>{current.title}</h3><p>{current.context}</p><div className="grid gap-3">{current.options.map((option, i) => <button className="secondary text-left" key={option.label} onClick={() => { setChoice(i); if (option.correct) setPassed((previous) => [...new Set([...previous, stage])]); }}>{option.label}</button>)}</div>
      {choice !== null && <p role="status" className="source-note"><strong>{current.options[choice].correct ? "决策通过" : "观察这个后果"}</strong><br />{current.options[choice].result}</p>}
    </div><p>已通过 {passed.length} / {lab.stages.length} 个决策。此处呈现预设教学情境，不调用模型、网页或本机工具。</p><button className="primary" disabled={passed.length !== lab.stages.length || completed} onClick={onComplete}>{completed ? "实验记录已保存" : "保存实验完成记录"}</button>
  </section>;
}
