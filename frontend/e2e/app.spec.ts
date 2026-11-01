import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Data: the recorded fixtures (Senado mandate 526: 4545, 5917, 5918; Câmara 220593 and 220714),
// loaded with `load_fixture_snapshot` into placar_e2e. No activity data is loaded there.

const OWN_ORIGINS = ["http://127.0.0.1:5174", "http://127.0.0.1:8001"];

async function watchRequests(page: Page) {
  const outside: string[] = [];
  page.on("request", (request) => {
    const url = request.url();
    if (!OWN_ORIGINS.some((origin) => url.startsWith(origin)) && !url.startsWith("data:")) outside.push(url);
  });
  return outside;
}

async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
}

async function expectSourcesOfficial(page: Page) {
  const hrefs = await page.locator('[data-testid="sourced-value"] a').evaluateAll((links) => links.map((a) => a.getAttribute("href")));
  expect(hrefs.length).toBeGreaterThan(0);
  for (const href of hrefs) expect(href).toMatch(/^https:\/\/([a-z0-9-]+\.)*(camara|senado)\.leg\.br\//);
}

test("officials list: snapshot date, insufficient data, official sources, accessible", async ({ page }) => {
  const outside = await watchRequests(page);
  await page.goto("/");
  await expect(page.getByText("Dados oficiais coletados em 01/11/2026.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Fernando Dueire" })).toBeVisible();
  await expect(page.getByText("Dados insuficientes").first()).toBeVisible();
  await expect(page.getByTestId("window-summary")).toContainText("01/02/2023 a 01/11/2026");
  await expectSourcesOfficial(page);
  await expectAccessible(page);
  expect(outside).toEqual([]);
});

test("profile: periods with reasons, metrics not loaded yet are not shown as numbers", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Fernando Dueire" }).click();
  await expect(page.getByRole("heading", { level: 1, name: /Fernando Dueire/ })).toBeVisible();
  await expect(page.getByText("Retorno do titular")).toBeVisible();
  await expect(page.getByText("Ainda não disponível").first()).toBeVisible();
  await expectSourcesOfficial(page);
  await expectAccessible(page);
});

test("compare: the window is shown above the side-by-side table", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: /Fernando Dueire/ }).check();
  await page.getByRole("checkbox", { name: /Jarbas Vasconcelos/ }).check();
  await page.getByRole("button", { name: /Comparar selecionados/ }).click();
  await expect(page.getByRole("heading", { name: "Comparação" })).toBeVisible();
  const summary = page.getByTestId("window-summary");
  const table = page.getByRole("table");
  await expect(summary).toBeVisible();
  const [summaryBox, tableBox] = await Promise.all([summary.boundingBox(), table.boundingBox()]);
  expect(summaryBox!.y).toBeLessThan(tableBox!.y);
  await expect(table.getByText("Dados insuficientes")).toBeVisible();
  await expectAccessible(page);
});

test("parties: membership change is labeled", async ({ page }) => {
  await page.goto("/partidos?casa=SENADO");
  await expect(page.getByRole("rowheader", { name: /PSD/ })).toContainText("Composição mudou no período");
  await expectAccessible(page);
});
