import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const chapter = JSON.parse(
  readFileSync("src/data/curriculum/chapter01.json", "utf8"),
);
test("learning, wrong answers, persistence, tests and exam", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("./");
  await expect(
    page.getByRole("heading", { name: "从零开始，系统掌握人工智能。" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/home-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("link", { name: "开始第一课" }).click();
  await expect(
    page.getByRole("heading", { name: "AI 学习路线概述", exact: true, level: 1 }),
  ).toBeVisible();
  await page.getByRole("button", { name: "收藏课程", exact: true }).click();
  await page
    .getByLabel("记录你的结果与发现")
    .fill("我的目标：做一张学习卡片。");
  const first = page.locator("#interact .quiz-card").first();
  await first.locator("input[type=radio]").nth(1).check();
  await first.getByRole("button", { name: "提交答案" }).click();
  await expect(first.locator(".feedback")).toContainText("答案有误");
  await page.reload();
  await expect(page.getByLabel("记录你的结果与发现")).toHaveValue(
    "我的目标：做一张学习卡片。",
  );
  await expect(
    page.getByRole("button", { name: "已收藏", exact: true }),
  ).toBeVisible();
  const cards = page.locator("#test .quiz-card");
  for (let i = 0; i < chapter.lessons[0].test.length; i++) {
    const q = chapter.lessons[0].test[i],
      card = cards.nth(i);
    if (q.type === "order") {
      for (let target = 0; target < q.answer.length; target++) {
        let labels = await card
          .locator(".order-item>span:nth-child(2)")
          .allTextContents();
        let current = labels.indexOf(q.answer[target]);
        while (current > target) {
          await card
            .getByRole("button", {
              name: `上移：${q.answer[target]}`,
              exact: true,
            })
            .click();
          current--;
        }
      }
    } else
      for (const answer of q.answer)
        await card.getByLabel(answer, { exact: false }).check();
  }
  await page
    .locator("#test")
    .getByRole("button", { name: "提交测试", exact: true })
    .click();
  await expect(page.locator("#test .result")).toContainText("100");
  await page.getByRole("button", { name: "标记为已完成", exact: true }).click();
  await page.goto("./#profile");
  await expect(page.locator(".stat-card").first()).toContainText("1");
  await page.goto("./#wrong");
  await expect(page.locator(".wrong-item")).toHaveCount(1);
  await page.getByRole("button", { name: "我已理解 · 标记为已解决" }).click();
  await expect(page.locator(".wrong-item")).toHaveCount(0);
  await page.goto("./#exam/1");
  await expect(page.locator(".quiz-card")).toHaveCount(12);
  const examCards = page.locator(".quiz-card");
  for (let i = 0; i < 12; i++) {
    const card = examCards.nth(i);
    if (await card.locator(".order-list").count())
      await card.getByRole("button", { name: "确认当前顺序" }).click();
    else if (await card.locator("input[type=checkbox]").count())
      await card.locator("input[type=checkbox]").first().check();
    else await card.locator("input[type=radio]").first().check();
  }
  await page.getByRole("button", { name: "提交测试", exact: true }).click();
  await expect(page.locator(".result")).toBeVisible();
  await page.reload();
  await page.goto("./#profile");
  await expect(page.locator(".exam-history")).toHaveCount(1);
  expect(errors).toEqual([]);
});
test("mobile navigation, search, all chapters and refresh under a subdirectory", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("./");
  await page.screenshot({
    path: "test-results/home-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "打开导航" }).click();
  await page
    .getByRole("link", { name: "全部课程", exact: true })
    .first()
    .click();
  await page.getByLabel("搜索课程").fill("异步");
  await expect(page.locator(".lesson-row")).toHaveCount(1);
  await page.locator(".lesson-row").click();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "异步编程", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/lesson-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  for (let i = 1; i <= 9; i++) {
    await page.goto(`./#lesson/${String(i).padStart(2, "0")}-01`);
    await expect(page.locator(".lesson-header h1")).toBeVisible();
    await expect(page.locator("#interact .quiz-card")).toHaveCount(3);
  }
});
test("malformed local storage is not silently overwritten", async ({
  page,
}) => {
  await page.goto("./");
  await page.evaluate(() =>
    localStorage.setItem("ai-academy.progress.v1", "{broken"),
  );
  await page.reload();
  await expect(page.locator(".warning")).toContainText("无法读取学习记录");
  expect(
    await page.evaluate(() => localStorage.getItem("ai-academy.progress.v1")),
  ).toBe("{broken");
});

test("reading layout respects reduced motion and keeps controls accessible", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("./#lesson/01-02");
  await expect(page.locator(".reading").first()).toBeVisible();
  expect(
    await page
      .locator(".page-content")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
  expect(
    await page
      .locator(".reading p")
      .first()
      .evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
  ).toBeGreaterThanOrEqual(16);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/lesson-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.locator(".sidebar")).toHaveClass(/open/);
  await page
    .getByRole("button", { name: "关闭导航", exact: true })
    .last()
    .click();
  await expect(page.locator(".sidebar")).not.toHaveClass(/open/);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("practice cards support copying, troubleshooting, material downloads and saved notes", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("./#lesson/03-11");
  const lab = page.locator(".practice-lab");
  await expect(lab.getByRole("heading", { name: "四个步骤有各自的过关条件" })).toBeVisible();
  await lab.getByRole("button", { name: "复制任务", exact: true }).click();
  await expect(lab.getByRole("status")).toContainText("已复制");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain("模拟报告阶段失败");
  await lab.locator("summary").click();
  await expect(lab.locator("details")).toHaveAttribute("open", "");
  await expect(lab.locator("details")).toContainText("不编造4条凑数");
  const download = page.waitForEvent("download");
  await lab.getByRole("link", { name: "状态文件示例" }).click();
  expect((await download).suggestedFilename()).toBe("state.example.json");
  await page.getByLabel("记录你的结果与发现").fill("来源表通过，报告阶段重试。");
  await page.reload();
  await expect(page.getByLabel("记录你的结果与发现")).toHaveValue("来源表通过，报告阶段重试。");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("./#lesson/02-02");
  await expect(page.locator(".practice-lab pre").first()).toContainText("Get-Location");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/practice-mobile.png", fullPage: true, animations: "disabled" });
  await page.goto("./#lesson/02-01");
  await expect(page.locator(".lesson-header h1")).toHaveText("检查已有工具与工作区");
  await expect(page.locator(".practice-lab")).not.toContainText("claude --help");
  await page.goto("./#lesson/03-10");
  await expect(page.locator(".practice-lab")).toContainText("每条引用用编辑器搜索核实");
});

test("all bundled practice resources work under the deployed subdirectory", async ({ request }) => {
  const files = ["README.md", "notes.md", "study.md", "study-card/SKILL.md", "slides-source.md", "learning.csv", "course.md", "update.md", "announcements.html", "announcements.csv", "state.example.json", "storyboard.md"];
  for (const file of files) {
    const response = await request.get(`./practice-kit/${file}`);
    expect(response.ok(), file).toBe(true);
    const body = await response.text();
    expect(body.length, file).toBeGreaterThan(40);
    if (file !== "announcements.html") expect(body, file).not.toContain('<div id="root">');
  }
  const state = await request.get("./practice-kit/state.example.json");
  expect((await state.json()).resumeFrom).toBe("report");
});
