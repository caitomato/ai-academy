import { useState } from "react";
import type { Question } from "../types";
import { grade } from "../progress";
import { Check, Lightbulb, RotateCcw, ArrowUp, ArrowDown } from "lucide-react";
const names = {
  single: "单选题",
  multiple: "多选题",
  boolean: "判断题",
  fill: "填空题",
  code: "代码阅读",
  order: "步骤排序",
};
export function AnswerInput({
  q,
  value,
  onChange,
  disabled = false,
}: {
  q: Question;
  value: string[];
  onChange: (a: string[]) => void;
  disabled?: boolean;
}) {
  if (q.type === "fill")
    return (
      <input
        aria-label="填写答案"
        disabled={disabled}
        className="answer-input"
        value={value[0] || ""}
        onChange={(e) => onChange([e.target.value])}
        placeholder="输入你的答案"
      />
    );
  if (q.type === "order") {
    const ordered = value.length ? value : q.options;
    function move(i: number, d: number) {
      const a = [...ordered];
      [a[i], a[i + d]] = [a[i + d], a[i]];
      onChange(a);
    }
    return (
      <div className="order-list">
        {ordered.map((o, i) => (
          <div className="order-item" key={o}>
            <span className="step-num">{i + 1}</span>
            <span>{o}</span>
            <button
              disabled={disabled || i === 0}
              aria-label={`上移：${o}`}
              onClick={() => move(i, -1)}
            >
              <ArrowUp size={16} />
            </button>
            <button
              disabled={disabled || i === ordered.length - 1}
              aria-label={`下移：${o}`}
              onClick={() => move(i, 1)}
            >
              <ArrowDown size={16} />
            </button>
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="options">
      {q.options.map((o, i) => (
        <label
          className={`option ${value.includes(o) ? "selected" : ""}`}
          key={o}
        >
          <input
            disabled={disabled}
            type={q.type === "multiple" ? "checkbox" : "radio"}
            name={q.id}
            checked={value.includes(o)}
            onChange={() =>
              onChange(
                q.type === "multiple"
                  ? value.includes(o)
                    ? value.filter((x) => x !== o)
                    : [...value, o]
                  : [o],
              )
            }
          />
          <span className="letter">{String.fromCharCode(65 + i)}</span>
          <span>{o}</span>
        </label>
      ))}
    </div>
  );
}
export function Feedback({ q, correct }: { q: Question; correct: boolean }) {
  return (
    <div
      className={`feedback ${correct ? "correct" : "incorrect"}`}
      role="status"
    >
      <strong>{correct ? "✓ 回答正确" : "再想一想，学习就发生在这里"}</strong>
      <p>正确答案：{q.answer.join(q.type === "order" ? " → " : "；")}</p>
      <p>{q.explanation}</p>
    </div>
  );
}
export function Quiz({
  q,
  onAnswer,
}: {
  q: Question;
  onAnswer: (q: Question, a: string[]) => void;
}) {
  const [value, setValue] = useState<string[]>(
    q.type === "order" ? q.options : [],
  );
  const [submitted, setSubmitted] = useState(false);
  const [hint, setHint] = useState(false);
  return (
    <article className="quiz-card">
      <span className="eyebrow">{names[q.type]}</span>
      <h3>{q.prompt}</h3>
      {q.code && (
        <pre>
          <code>{q.code}</code>
        </pre>
      )}
      <AnswerInput
        q={q}
        value={value}
        onChange={setValue}
        disabled={submitted}
      />
      <div className="quiz-actions">
        {submitted ? (
          <button
            className="secondary"
            onClick={() => {
              setSubmitted(false);
              setValue(q.type === "order" ? q.options : []);
            }}
          >
            <RotateCcw size={16} />
            重新答题
          </button>
        ) : (
          <button
            className="primary"
            disabled={!value.length || !value[0]?.trim()}
            onClick={() => {
              setSubmitted(true);
              onAnswer(q, value);
            }}
          >
            <Check size={16} />
            提交答案
          </button>
        )}
        <button className="text-button" onClick={() => setHint(!hint)}>
          <Lightbulb size={16} />
          {hint ? "收起提示" : "给我提示"}
        </button>
      </div>
      {hint && <p className="hint">{q.hint}</p>}
      {submitted && <Feedback q={q} correct={grade(q, value)} />}
    </article>
  );
}
export function Test({
  title,
  items,
  onFinish,
}: {
  title: string;
  items: Question[];
  onFinish: (answers: Record<string, string[]>, score: number) => void;
}) {
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [result, setResult] = useState<number | null>(null);
  const valid = items.every(
    (q) => answers[q.id]?.length && answers[q.id][0]?.trim(),
  );
  return (
    <section className="test-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">CHECK YOUR UNDERSTANDING</span>
          <h2>{title}</h2>
        </div>
        <span className="tag">{items.length} 题 · 达到 80 分即掌握</span>
      </div>
      {items.map((q, i) => (
        <article className="quiz-card" key={q.id}>
          <span className="eyebrow">
            {i + 1} / {items.length} · {names[q.type]}
          </span>
          <h3>{q.prompt}</h3>
          {q.code && (
            <pre>
              <code>{q.code}</code>
            </pre>
          )}
          <AnswerInput
            q={q}
            disabled={result !== null}
            value={answers[q.id] || []}
            onChange={(a) => setAnswers({ ...answers, [q.id]: a })}
          />
          {q.type === "order" && !answers[q.id] && (
            <button
              className="secondary"
              onClick={() => setAnswers({ ...answers, [q.id]: q.options })}
            >
              确认当前顺序
            </button>
          )}
          {result !== null && (
            <Feedback q={q} correct={grade(q, answers[q.id] || [])} />
          )}
        </article>
      ))}
      {result === null ? (
        <>
          <p className="muted">
            已作答{" "}
            {
              Object.keys(answers).filter(
                (k) => answers[k].length && answers[k][0]?.trim(),
              ).length
            }{" "}
            / {items.length} 题。提交后统一显示答案与解析。
          </p>
          <button
            className="primary"
            disabled={!valid}
            onClick={() => {
              const score = Math.round(
                (items.filter((q) => grade(q, answers[q.id] || [])).length /
                  items.length) *
                  100,
              );
              setResult(score);
              onFinish(answers, score);
            }}
          >
            提交测试
          </button>
        </>
      ) : (
        <div className="result" role="status">
          <strong>
            {result} <small>分</small>
          </strong>
          <h3>
            {result >= 80 ? "已掌握，继续向前！" : "先复习错题，再试一次"}
          </h3>
          <p>错题已加入错题本。可以查看上方逐题解析。</p>
          <button
            className="secondary"
            onClick={() => {
              setResult(null);
              setAnswers({});
            }}
          >
            重新测试
          </button>
        </div>
      )}
    </section>
  );
}
