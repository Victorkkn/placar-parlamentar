import { defineConfig, devices } from "@playwright/test";

// End-to-end tests (Phase C5, decision 0011 item 16): Chromium only, offline, against a backend
// loaded with the recorded fixtures in its own database (placar_e2e).
const API_PORT = 8001;
const WEB_PORT = 5174;

export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  retries: 0,
  reporter: process.env.CI ? "github" : "list",
  use: { baseURL: `http://127.0.0.1:${WEB_PORT}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run python manage.py runserver 127.0.0.1:${API_PORT} --noreload`,
      cwd: "../backend",
      env: { DATABASE_NAME: "placar_e2e" },
      url: `http://127.0.0.1:${API_PORT}/api/meta`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npx vite --port ${WEB_PORT} --strictPort`,
      env: { PLACAR_API_TARGET: `http://127.0.0.1:${API_PORT}` },
      url: `http://127.0.0.1:${WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
