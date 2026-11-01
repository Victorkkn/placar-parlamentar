import { describe, expect, it } from "vitest";

import { meta } from "../test/data";
import { apiWindowParams, readFilters, windowFor } from "./filters";
import { formatDate, formatInteger, formatPercent } from "./format";

describe("format (pt-BR)", () => {
  it("formats dates without time-zone shifts", () => {
    expect(formatDate("2023-02-01")).toBe("01/02/2023");
    expect(formatDate("2023-12-31T23:59")).toBe("31/12/2023");
    expect(formatDate(null)).toBe("—");
  });

  it("formats numbers", () => {
    expect(formatInteger(1370)).toBe("1.370");
    expect(formatPercent(0.511679)).toBe("51,2%");
  });
});

describe("filters from the URL", () => {
  const params = (q: string) => new URLSearchParams(q);

  it("defaults to the current legislature and the API's default share", () => {
    const f = readFilters(params(""), meta);
    expect(f).toMatchObject({ preset: "legislatura", mode: "proporcao", minimum: 50 });
    expect(windowFor(f, meta)).toEqual({ start: "2023-02-01", end: "2026-11-01" });
    expect(apiWindowParams(f, meta)).toEqual({ start: "2023-02-01", end: "2026-11-01", min_share: 0.5 });
  });

  it("last 2 years is the 730 days up to the snapshot date", () => {
    const f = readFilters(params("periodo=2anos"), meta);
    expect(windowFor(f, meta)).toEqual({ start: "2024-11-02", end: "2026-11-01" });
  });

  it("custom window and a threshold in days", () => {
    const f = readFilters(params("periodo=personalizado&inicio=2024-01-01&fim=2024-06-30&modo=dias&minimo=90"), meta);
    expect(apiWindowParams(f, meta)).toEqual({ start: "2024-01-01", end: "2024-06-30", min_days: 90 });
  });

  it("clamps a share outside 0–100%", () => {
    expect(apiWindowParams(readFilters(params("minimo=150"), meta), meta).min_share).toBe(1);
    expect(apiWindowParams(readFilters(params("minimo=-5"), meta), meta).min_share).toBe(0);
  });

  it("ignores a non-numeric minimum", () => {
    expect(readFilters(params("minimo=abc"), meta).minimum).toBe(50);
  });
});
