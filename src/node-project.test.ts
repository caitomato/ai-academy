import { describe, expect, it } from "vitest";
import { commandTrials, startupCases } from "./components/NodeProject";
import { lessons, questionById } from "./data";
import { emptyState, parseState } from "./progress";

describe("independent project course", () => {
  it("provides all required teaching stages with stable IDs", () => {
    const lesson = lessons.find((item) => item.id === "02-04")!;
    expect(lesson.title).toBe("让 JavaScript 在电脑上运行");
    expect(lesson.experience?.walkthrough).toHaveLength(8);
    expect(lesson.experience?.troubleshooting).toHaveLength(5);
    expect(lesson.experience?.fields.map((item) => item.name)).toEqual(["scripts", "dependencies", "devDependencies"]);
    for (const suffix of ["p1", "p2", "p3", "t1", "t2", "t3", "t4"]) expect(questionById[`02-04-${suffix}`]).toBeTruthy();
    expect(commandTrials).toHaveLength(4);
    expect(startupCases).toHaveLength(6);
    expect(startupCases.every((item) => item.options[item.correct])).toBe(true);
  });
  it("keeps prior experiment records without granting new completion", () => {
    const previous = { ...emptyState(), tasks: ["02-04:video-sim", "02-04"], completed: ["02-04"], bookmarks: ["02-04"], scores: { "02-04": 100 } };
    const restored = parseState(JSON.stringify(previous));
    expect(restored).toEqual(previous);
    expect(restored.tasks).not.toContain("02-04:project-lab-v2");
  });
  it("publishes learning data without production traces or rote-position prompts", () => {
    const serialized = JSON.stringify(lessons);
    expect(serialized).not.toMatch(/视频融合|视频知识点|\.mp4|课件第\s*\d|逐帧核对|videoId|第一个关键词|第一个词/);
    expect(lessons.every((lesson) => lesson.introduction && lesson.summary)).toBe(true);
  });
});
