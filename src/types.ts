export type Question = {
  id: string;
  lessonId: string;
  type: "single" | "multiple" | "boolean" | "fill" | "code" | "order";
  prompt: string;
  options: string[];
  answer: string[];
  explanation: string;
  hint: string;
  code?: string;
};
export type Lesson = {
  id: string;
  chapterId: number;
  title: string;
  pages: string;
  minutes: number;
  objectives: string[];
  sections: { title: string; text: string }[];
  example: string;
  task: string;
  steps: string[];
  terms: string[];
  misconception: string;
  code?: string;
  questions: Question[];
  test: Question[];
  sourceNote?: string;
};
export type Chapter = {
  id: number;
  title: string;
  description: string;
  lessons: Lesson[];
};
export type Attempt = {
  id: string;
  questionId: string;
  answer: string[];
  correct: boolean;
  date: string;
};
export type State = {
  version: 1;
  completed: string[];
  bookmarks: string[];
  recent: string[];
  attempts: Attempt[];
  resolved: string[];
  scores: Record<string, number>;
  exams: { chapterId: number; score: number; date: string }[];
  days: string[];
  notes: Record<string, string>;
  taskDays: string[];
  tasks: string[];
};
