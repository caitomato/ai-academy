import { describe, it, expect } from "vitest";
import { chapters, lessons, questions } from "./data";
import { emptyState, grade, parseState, sample } from "./progress";
describe("curriculum contract", () => {
  it("covers nine chapters with complete lessons and unique question IDs", () => {
    expect(chapters).toHaveLength(9);
    expect(lessons).toHaveLength(83);
    expect(new Set(questions.map((q) => q.id)).size).toBe(questions.length);
    for (const l of lessons) {
      expect(l.questions.length).toBeGreaterThanOrEqual(3);
      expect(l.test.length).toBeGreaterThanOrEqual(3);
      expect(l.test.length).toBeLessThanOrEqual(5);
      expect(l.pages).toBeTruthy();
      expect(l.example.length).toBeGreaterThan(20);
      expect(l.steps.length).toBe(4);
    }
    expect(new Set(questions.map((q) => q.type)).size).toBe(6);
  });
  it("accepts all supplied answer keys and rejects incomplete answers", () => {
    for (const q of questions) {
      expect(grade(q, q.answer), q.id).toBe(true);
      expect(grade(q, []), q.id).toBe(false);
      if (q.type !== "fill")
        expect(
          q.answer.every((a) => q.options.includes(a)),
          q.id,
        ).toBe(true);
    }
  });
  it("checks multiple choice as a set, ordering as a sequence, and normalizes fill input", () => {
    const multi = questions.find((q) => q.type === "multiple")!;
    expect(grade(multi, [...multi.answer].reverse())).toBe(true);
    expect(grade(multi, [multi.answer[0], multi.answer[0]])).toBe(false);
    const order = questions.find((q) => q.type === "order")!;
    expect(grade(order, [...order.answer].reverse())).toBe(false);
    const fill = questions.find(
      (q) => q.type === "fill" && q.answer[0] === "Token",
    )!;
    expect(grade(fill, ["  TOKEN  "])).toBe(true);
  });
  it("samples without duplicates and never mutates the pool", () => {
    const pool = [1, 2, 3, 4, 5];
    const result = sample(pool, 4);
    expect(new Set(result).size).toBe(4);
    expect(pool).toEqual([1, 2, 3, 4, 5]);
  });
});
describe("persistence", () => {
  it("round-trips progress and notes", () => {
    const state = {
      ...emptyState(),
      completed: ["01-01"],
      notes: { "01-01": "练习完成" },
      scores: { "01-01": 100 },
    };
    expect(parseState(JSON.stringify(state))).toEqual(state);
  });
  it("rejects corrupt imports rather than replacing valid records", () => {
    expect(() => parseState("{")).toThrow();
    expect(() => parseState("{}")).toThrow();
    expect(() =>
      parseState(JSON.stringify({ ...emptyState(), scores: { x: 200 } })),
    ).toThrow();
    expect(() =>
      parseState(
        JSON.stringify({
          ...emptyState(),
          attempts: [{ questionId: "x", answer: "bad" }],
        }),
      ),
    ).toThrow();
  });
});
