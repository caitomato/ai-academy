import { describe, it, expect } from "vitest";
import { chapters, lessons } from "./data";
import { emptyState, parseState } from "./progress";
describe("Web V2 curriculum contract", () => {
  it("has reviewed first chapter, prerequisites and complete decision branches", () => {
    for (const lesson of chapters[0].lessons) {
      expect(lesson.developmentStatus).toBe("reviewed");
      expect(lesson.analogy).toBeTruthy();
      expect(lesson.decisionLab?.stages).toHaveLength(2);
      for (const stage of lesson.decisionLab!.stages) expect(stage.options.filter((option) => option.correct)).toHaveLength(1);
      for (const prerequisite of lesson.prerequisites || []) expect(lessons.some((item) => item.id === prerequisite)).toBe(true);
    }
  });
  it("preserves old backups and validates new study-time records", () => {
    const old = emptyState();
    expect(parseState(JSON.stringify(old))).toEqual(old);
    expect(parseState(JSON.stringify({ ...old, studySeconds: { "01-01": 45 } })).studySeconds?.["01-01"]).toBe(45);
    expect(() => parseState(JSON.stringify({ ...old, studySeconds: { x: -1 } }))).toThrow();
  });
});
