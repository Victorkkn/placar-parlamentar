import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { text } from "./pt-BR";

// Rule 4 / decision 0011 item 15: no banned wording in user-facing text.
// Tests run from frontend/; the list lives in the repo docs.
const listPath = resolve(process.cwd(), "../docs/wording/banned-pt-BR.txt");
const normalize = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const banned = readFileSync(listPath, "utf8")
  .split("\n")
  .map((l) => l.trim())
  .filter((l) => l && !l.startsWith("#"))
  .map(normalize);

function strings(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (typeof value === "function") return strings((value as (...a: unknown[]) => unknown)("1", "2", "3"));
  if (Array.isArray(value)) return value.flatMap(strings);
  if (value && typeof value === "object") return Object.values(value).flatMap(strings);
  return [];
}

describe("pt-BR text", () => {
  it("has a non-empty banned list", () => {
    expect(banned.length).toBeGreaterThan(10);
  });

  it("contains no banned wording", () => {
    const found = strings(text).flatMap((s) => {
      const words = ` ${normalize(s).replace(/[^\p{L}\s]/gu, " ")} `;
      return banned.filter((b) => words.includes(` ${b} `)).map((b) => `${b} in "${s}"`);
    });
    expect(found).toEqual([]);
  });
});
