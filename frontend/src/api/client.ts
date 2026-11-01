import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

// Calls go to our own server only (decision 0009, item 11); Vite proxies /api in development.
// `fetch` is looked up at call time, so test tools that replace it are respected.
export const api = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (input: Request) => globalThis.fetch(input),
});

export type Schemas = components["schemas"];
export type Source = Schemas["Source"];
export type Metric = Schemas["MetricOut"];

export class ApiError extends Error {}

export async function unwrap<T>(promise: Promise<{ data?: T; error?: unknown }>): Promise<T> {
  const { data, error } = await promise;
  if (error !== undefined || data === undefined) {
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    throw new ApiError(typeof detail === "string" ? detail : "Erro ao carregar os dados.");
  }
  return data;
}
