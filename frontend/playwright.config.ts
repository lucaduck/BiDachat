import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 180000,
  expect: { timeout: 15000 },
  use: {
    baseURL: process.env.QA_BASE_URL ?? "http://127.0.0.1:3001",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [
    ["list"],
    ["html", { outputFolder: "../docs/qa/frontend/playwright-report", open: "never" }],
  ],
  outputDir: "../docs/qa/frontend/test-results",
});
