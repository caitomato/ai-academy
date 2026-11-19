import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const lesson = JSON.parse(readFileSync("src/data/curriculum/chapter02.json", "utf8")).lessons.find((item: { id: string }) => item.id === "02-04");

for (const mobile of [false, true]) test(`complete Node course on ${mobile ? "mobile" : "desktop"}`, async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  await page.setViewportSize(mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 });
  await page.goto("./#lesson/02-04");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("让 JavaScript 在电脑上运行");
  await expect(page.locator("body")).not.toContainText("视频融合");
  await expect(page.locator(".workflow-rail > li")).toHaveCount(8);
  const tree = page.getByRole("group", { name: "项目目录", exact: true });
  for (const file of lesson.experience.files) {
    await tree.getByRole("button", { name: file.name.trim(), exact: false }).click();
    await expect(page.locator(".file-detail h3")).toHaveText(file.name);
    await expect(page.locator(".file-detail")).toContainText(file.description);
  }
  const a = page.locator(".experiment").nth(0);
  const choices = ["查看版本", "查看版本", "进入交互环境", "执行程序"];
  await a.getByRole("button", { name: "执行程序", exact: true }).click();
  await expect(a.getByRole("status")).toContainText("再试一次");
  for (let i = 0; i < 4; i++) {
    await a.getByRole("group", { name: "选择命令" }).getByRole("button").nth(i).click();
    await a.getByRole("button", { name: choices[i], exact: true }).click();
    await expect(a.getByRole("status")).toContainText("判断正确");
  }
  const b = page.locator(".experiment").nth(1);
  for (let i = 0; i < 3; i++) {
    await b.getByRole("group", { name: "配置字段" }).getByRole("button").nth(i).click();
    await expect(b).toContainText(lesson.experience.fields[i].explanation);
    await b.getByRole("button", { name: "记录本字段已阅读", exact: true }).click();
  }
  const c = page.locator(".experiment").nth(2);
  for (let i = 0; i < 6; i++) {
    await c.getByRole("group", { name: "故障情境" }).getByRole("button").nth(i).click();
    await c.locator(".scenario-options button").nth((i % 3 + 1) % 3).click();
    await expect(c.getByRole("status")).toContainText("没有对应");
    await c.locator(".scenario-options button").nth(i % 3).click();
    await expect(c.getByRole("status")).toContainText("处理正确");
  }
  await page.getByRole("button", { name: "保存本课实验完成记录", exact: true }).click();
  for (const item of lesson.experience.troubleshooting) {
    const detail = page.locator(".diagnosis-list details").filter({ hasText: item.symptom });
    await detail.locator("summary").click();
    await expect(detail).toContainText(item.resolution);
  }
  await page.screenshot({ path: `test-results/node-${mobile ? "mobile" : "desktop"}.png`, fullPage: true, animations: "disabled" });
  for (const [section, questions] of [["interact", lesson.questions], ["test", lesson.test]] as const) {
    const cards = page.locator(`#${section} .quiz-card`);
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i], card = cards.nth(i);
      if (q.type === "order") {
        for (let target = 0; target < q.answer.length; target++) {
          let order = await card.locator(".order-item > span:nth-child(2)").allTextContents();
          let position = order.indexOf(q.answer[target]);
          while (position > target) { await card.getByRole("button", { name: `上移：${q.answer[target]}`, exact: true }).click(); position--; }
        }
      } else for (const answer of q.answer) await card.locator("label").filter({ hasText: answer }).locator("input").check();
      if (section === "interact") { await card.getByRole("button", { name: "提交答案", exact: true }).click(); await expect(card.locator(".feedback")).toContainText("回答正确"); }
    }
  }
  await page.locator("#test").getByRole("button", { name: /提交/ }).click();
  await expect(page.locator("#test")).toContainText("100");
  await page.reload();
  await expect(page.locator(".experiment-complete")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
