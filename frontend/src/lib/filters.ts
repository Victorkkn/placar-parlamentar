import { useSearchParams } from "react-router";

import type { Schemas } from "../api/client";

/** Filters live in the URL so every view can be shared (decision 0009, item 5). */
export type Preset = "legislatura" | "2anos" | "personalizado";
export type ThresholdMode = "proporcao" | "dias";

export interface Filters {
  preset: Preset;
  start?: string;
  end?: string;
  mode: ThresholdMode;
  minimum: number;
}

export function readFilters(params: URLSearchParams, meta?: Schemas["MetaOut"]): Filters {
  const preset = (params.get("periodo") as Preset) || "legislatura";
  const mode = (params.get("modo") as ThresholdMode) || "proporcao";
  const raw = params.get("minimo");
  const fallback = mode === "dias" ? 0 : Math.round((meta?.default_min_share ?? 0.5) * 100);
  const minimum = raw !== null && raw !== "" && !Number.isNaN(Number(raw)) ? Number(raw) : fallback;
  return { preset, start: params.get("inicio") ?? undefined, end: params.get("fim") ?? undefined, mode, minimum };
}

export function windowFor(filters: Filters, meta?: Schemas["MetaOut"]): { start?: string; end?: string } {
  const snapshot = meta?.snapshot_date ?? undefined;
  if (filters.preset === "personalizado") return { start: filters.start, end: filters.end };
  if (filters.preset === "2anos" && snapshot) {
    const end = new Date(`${snapshot}T00:00:00Z`);
    const start = new Date(end.getTime() - 729 * 86_400_000);
    return { start: start.toISOString().slice(0, 10), end: snapshot };
  }
  return { start: meta?.legislature_start ?? undefined, end: snapshot };
}

export function apiWindowParams(filters: Filters, meta?: Schemas["MetaOut"]) {
  const { start, end } = windowFor(filters, meta);
  const threshold =
    filters.mode === "dias" ? { min_days: Math.max(0, Math.round(filters.minimum)) } : { min_share: Math.min(1, Math.max(0, filters.minimum / 100)) };
  return { ...(start ? { start } : {}), ...(end ? { end } : {}), ...threshold };
}

export function useFilters() {
  const [params, setParams] = useSearchParams();
  const update = (changes: Record<string, string | undefined>) => {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value === undefined || value === "") next.delete(key);
      else next.set(key, value);
    }
    if (!("pagina" in changes)) next.delete("pagina");
    setParams(next);
  };
  return { params, update };
}
