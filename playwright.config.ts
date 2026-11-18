import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:4173/ai-academy/",
    channel: process.env.CI ? undefined : "msedge",
    headless: true,
    viewport: { width: 1440, height: 1000 },
  },
  webServer: {
    command: "npm run preview -- --port 4173 --base /ai-academy/",
    url: "http://127.0.0.1:4173/ai-academy/",
    reuseExistingServer: !process.env.CI,
  },
});
