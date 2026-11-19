import { test, expect } from '@playwright/test';

test('published version and lightweight installer are accessible without exposing student data', async ({ page, request }) => {
  await page.goto('./');
  const section = page.getByRole('region', { name: '课程更新' });
  await expect(section.getByRole('heading', { name: '最新课程版本' })).toBeVisible();
  await section.getByText('本地课程如何更新？', { exact: true }).click();
  await expect(section).toContainText('检查 AI Academy 课程更新');
  await expect(section).toContainText('重大教学逻辑变化会先征求确认');
  const installer = await request.get('./downloads/ai-academy-bootstrap.zip');
  expect(installer.ok()).toBeTruthy();
  const data = await installer.body();
  expect(data.subarray(0, 2).toString()).toBe('PK');
  expect(data.byteLength).toBeLessThan(100000);
});
