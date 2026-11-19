import type { Question, State } from "./types";
import migrations from "./data/migrations.json";

export function migrateState(state: State, mapping: { lessonIds: Record<string, string>; questionIds: Record<string, string> } = migrations): State {
  const alias = (items: string[], ids: Record<string, string>) => [...new Set(items.flatMap((id) => ids[id] ? [id, ids[id]] : [id]))];
  const records = <T,>(values: Record<string, T>) => {
    const next = { ...values };
    for (const [old, id] of Object.entries(mapping.lessonIds)) if (old in values && !(id in next)) next[id] = values[old];
    return next;
  };
  return { ...state, completed: alias(state.completed, mapping.lessonIds), bookmarks: alias(state.bookmarks, mapping.lessonIds), recent: alias(state.recent, mapping.lessonIds), tasks: alias(state.tasks, mapping.lessonIds), resolved: alias(state.resolved, mapping.questionIds), scores: records(state.scores), notes: records(state.notes), attempts: state.attempts.map((a) => ({ ...a, questionId: mapping.questionIds[a.questionId] || a.questionId })) };
}
export const STORAGE_KEY = "ai-academy.progress.v1";
export const emptyState = (): State => ({
  version: 1,
  completed: [],
  bookmarks: [],
  recent: [],
  attempts: [],
  resolved: [],
  scores: {},
  exams: [],
  days: [],
  notes: {},
  taskDays: [],
  tasks: [],
});
export function grade(q: Question, answer: string[]) {
  const normalize = (s: string) =>
    s.normalize("NFKC").trim().toLocaleLowerCase();
  if (q.type === "fill")
    return (
      answer.length === 1 &&
      q.answer.some((a) => normalize(a) === normalize(answer[0]))
    );
  if (q.type === "order")
    return (
      answer.length === q.answer.length &&
      answer.every((a, i) => a === q.answer[i])
    );
  return (
    answer.length === q.answer.length &&
    new Set(answer).size === answer.length &&
    q.answer.every((a) => answer.includes(a))
  );
}
export function parseState(raw: string): State {
  const s = JSON.parse(raw);
  const strings = (v: unknown) =>
    Array.isArray(v) && v.every((x) => typeof x === "string");
  if (
    !s ||
    s.version !== 1 ||
    !["completed", "bookmarks", "recent", "resolved", "days", "tasks"].every(
      (k) => strings(s[k]),
    ) ||
    !Array.isArray(s.attempts) ||
    !s.attempts.every(
      (a: any) =>
        typeof a.id === "string" &&
        typeof a.questionId === "string" &&
        strings(a.answer) &&
        typeof a.correct === "boolean" &&
        typeof a.date === "string",
    ) ||
    !Array.isArray(s.exams) ||
    !s.exams.every(
      (e: any) =>
        Number.isInteger(e.chapterId) &&
        e.chapterId >= 1 &&
        e.chapterId <= 9 &&
        Number.isFinite(e.score) &&
        e.score >= 0 &&
        e.score <= 100 &&
        typeof e.date === "string",
    ) ||
    !s.scores ||
    Array.isArray(s.scores) ||
    typeof s.scores !== "object" ||
    !Object.values(s.scores).every(
      (v) => typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 100,
    ) ||
    !s.notes ||
    Array.isArray(s.notes) ||
    typeof s.notes !== "object" ||
    !Object.values(s.notes).every((v) => typeof v === "string")
  )
    throw new Error("备份格式不正确，原有记录未改变。");
  if (s.taskDays !== undefined && !strings(s.taskDays))
    throw new Error("实践日期格式不正确。");
  if (s.studySeconds !== undefined && (!s.studySeconds || Array.isArray(s.studySeconds) || typeof s.studySeconds !== "object" || !Object.values(s.studySeconds).every((v) => typeof v === "number" && Number.isFinite(v) && v >= 0))) throw new Error("学习时长格式不正确。");
  return migrateState({ ...s, taskDays: s.taskDays || [] });
}
export function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
export function streak(days: string[]) {
  let count = 0;
  const date = new Date();
  const key = () =>
    `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  if (!days.includes(key())) date.setDate(date.getDate() - 1);
  while (days.includes(key())) {
    count++;
    date.setDate(date.getDate() - 1);
  }
  return count;
}
export function sample<T>(items: T[], count: number): T[] {
  const a = [...items];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, count);
}
