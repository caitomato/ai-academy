import { test, expect } from "@playwright/test";

test("video sample accepts commands and preserves only explicit simulation completion", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("./#lesson/02-04");
  await expect(page.getByRole("heading", { name: "从“装好了”到“确实能运行”" })).toBeVisible();
  const input = page.getByLabel(/输入命令/);
  await input.fill("npm install unknown");
  await page.getByRole("button", { name: "运行模拟", exact: true }).click();
  await expect(page.locator(".terminal-simulator")).toContainText("请对照本步命令");
  for (const command of ["node --version", "npm --version", "node", "let a=10", "let b=20", "console.log(a+b)", ".exit"]) {
    await input.fill(command);
    await page.getByRole("button", { name: "运行模拟", exact: true }).click();
  }
  await page.getByRole("button", { name: "记录模拟实操完成", exact: true }).click();
  await page.reload();
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem("ai-academy.progress.v1")!).tasks)).toContain("02-04:video-sim");
  await expect(page.locator("#interact .quiz-card")).toHaveCount(3);
  await expect(page.locator("#test .quiz-card")).toHaveCount(4);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
