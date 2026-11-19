import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const chapter = JSON.parse(readFileSync("content/chapters/chapter01.json", "utf8"));
test("all first-chapter labs, lesson routes and backup roundtrip", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", (error) => errors.push(error.message));
  for (const lesson of chapter.lessons) {
    await page.goto(`./#lesson/${lesson.id}`);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(lesson.title);
    const lab = page.locator("#decision-lab");
    for (let i = 0; i < lesson.decisionLab.stages.length; i++) {
      await lab.getByRole("group", { name: "实验阶段" }).getByRole("button").nth(i).click();
      const stage = lesson.decisionLab.stages[i];
      for (const option of stage.options) {
        await lab.getByRole("button", { name: option.label, exact: true }).click();
        await expect(lab.getByRole("status")).toContainText(option.result);
      }
    }
    await lab.getByRole("button", { name: "保存实验完成记录", exact: true }).click();
    await expect(lab.getByRole("button", { name: "实验记录已保存" })).toBeDisabled();
  }
  const chapters = Array.from({ length: 9 }, (_, i) => JSON.parse(readFileSync(`content/chapters/chapter${String(i + 1).padStart(2, "0")}.json`, "utf8")));
  for (const lesson of chapters.flatMap((item) => item.lessons)) {
    await page.goto(`./#lesson/${lesson.id}`);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(lesson.title);
    await expect(page.locator("#interact .quiz-card")).toHaveCount(3);
    await expect(page.locator("#test .quiz-card")).toHaveCount(4);
  }
  await page.goto("./#profile");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出备份", exact: true }).click();
  const download = await downloadPromise;
  const backup = await download.path();
  page.on("dialog", (dialog) => dialog.accept());
  await page.getByLabel("导入备份", { exact: true }).setInputFiles(backup!);
  await expect(page.getByText("学习记录已导入。", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("./#lesson/01-05");
  await expect(page.locator("#decision-lab")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
