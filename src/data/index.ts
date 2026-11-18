import type { Chapter } from "../types";
const files = import.meta.glob<Chapter>("./curriculum/*.json", {
  eager: true,
  import: "default",
});
export const chapters = Object.values(files).sort((a, b) => a.id - b.id);
export const lessons = chapters.flatMap((c) => c.lessons);
export const questions = lessons.flatMap((l) => [...l.questions, ...l.test]);
export const lessonById = Object.fromEntries(lessons.map((l) => [l.id, l]));
export const questionById = Object.fromEntries(questions.map((q) => [q.id, q]));
