import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import * as data from "./data";

export const handlers = [
  http.get("*/api/meta", () => HttpResponse.json(data.meta)),
  http.get("*/api/officials", () => HttpResponse.json(data.officialsPage)),
  http.get("*/api/officials/:id", () => HttpResponse.json(data.detailA)),
  http.get("*/api/compare", () => HttpResponse.json(data.compare)),
  http.get("*/api/parties", () => HttpResponse.json(data.parties)),
];

export const server = setupServer(...handlers);
