import { describe, expect, it } from "vitest";
import videos from "./data/video-index.json";
import { terminalAnswer } from "./components/VideoLesson";

describe("video source boundaries", () => {
  it("keeps inventory coverage honest and private sources out of published data", () => {
    expect(videos).toHaveLength(35);
    expect(new Set(videos.map((v) => v.videoId)).size).toBe(35);
    expect(videos.filter((v) => v.duration === null)).toHaveLength(3);
    expect(videos.every((v) => v.transcript === null && !v.status.qualityPassed)).toBe(true);
    expect(JSON.stringify(videos)).not.toMatch(/pan\.baidu|提取码|BDUSS|https?:/i);
  });
  it("accepts whitespace variants but never executes arbitrary JavaScript", () => {
    expect(terminalAnswer(3, "let a=10;")).toBe(true);
    expect(terminalAnswer(5, "console.log(a+b)")).toBe(true);
    expect(terminalAnswer(0, "npm install something")).toBe(false);
    expect(terminalAnswer(3, "alert(document.cookie)")).toBe(false);
    expect(terminalAnswer(7, "")).toBe(false);
  });
});
