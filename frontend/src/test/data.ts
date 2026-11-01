// SYNTHETIC API responses for component tests (decision 0011, item 6). Never shown in the app.
import type { Schemas } from "../api/client";

const src = (path: string): Schemas["Source"] => ({ api_url: `https://dadosabertos.camara.leg.br/api/v2/${path}`, public_url: null, label: "" });
const window: Schemas["Window"] = { start: "2023-02-01", end: "2026-11-01", days: 1370 };
const threshold: Schemas["Threshold"] = { min_days: null, min_share: 0.5 };

export const meta: Schemas["MetaOut"] = {
  snapshot_date: "2026-11-01",
  legislature: 57,
  legislature_start: "2023-02-01",
  legislature_end: "2027-01-31",
  earliest_date: "1988-10-05",
  default_min_share: 0.5,
  houses: [
    { house: "CAMARA", people_loaded_on: "2026-11-01", activity_loaded_on: "2026-11-01", data_fetched_until: null, metrics: ["plenary_attendance"] },
    { house: "SENADO", people_loaded_on: "2026-11-01", activity_loaded_on: null, data_fetched_until: null, metrics: [] },
  ],
};

const coverage = (days: number, share: number): Schemas["CoverageOut"] => ({
  days_in_office: days,
  window_days: 1370,
  share,
  periods: [{ start: "2023-02-01", end: "2025-01-01" }],
  sources: [src("deputados/1/historico")],
});

export const summaryA: Schemas["OfficialSummary"] = {
  id: 1, house: "CAMARA", house_id: 101, name: "Pessoa A", state: "SP", party: "P1", photo_url: null, page_url: null,
  coverage: coverage(701, 0.511679), sufficient: true, sources: [src("deputados?idLegislatura=57")],
};
export const summaryB: Schemas["OfficialSummary"] = {
  ...summaryA, id: 2, house_id: 102, name: "Pessoa B", party: "P2", coverage: coverage(30, 0.0219), sufficient: false,
};

export const officialsPage = {
  window, threshold, total: 2, page: 1, page_size: 50, items: [summaryA, summaryB], not_in_office: 3,
} satisfies Schemas["OfficialsPageOut"];

const metrics: Schemas["MetricOut"][] = [
  { key: "plenary_attendance", available: true, numerator: 80, denominator: 100, value: 0.8, per_365_days_in_office: null, details: { leave_days: 12 }, sources: [src("eventos/1/deputados")], reason: null },
  { key: "bills_authored", available: true, numerator: 7, denominator: null, value: 7, per_365_days_in_office: 3.6448, details: {}, sources: [src("proposicoes?idDeputadoAutor=101")], reason: null },
  { key: "vote_participation", available: true, numerator: 0, denominator: 0, value: null, per_365_days_in_office: null, details: {}, sources: [], reason: null },
  { key: "speeches", available: false, reason: "not_loaded_yet", numerator: null, denominator: null, value: null, per_365_days_in_office: null, details: {}, sources: [] },
];

export const detailA: Schemas["OfficialDetail"] = {
  window, threshold, official: summaryA, metrics,
  periods: [{ start: "2023-02-01", end: "2025-01-01", start_reason: "ELECTED_OATH", end_reason: "RESIGNATION", sources: [src("deputados/101/historico")] }],
  affiliations: [{ party: "P1", start: "2023-02-01", end: null, precision: "AT_EVENT", sources: [src("deputados/101/historico")] }],
  summary: {
    kind: "template",
    sentences: [
      { text: "Entre 01/02/2023 e 01/11/2026, Pessoa A esteve no cargo em 700 de 1.370 dias (51,1%).", sources: [src("deputados/101/historico")] },
      { text: "Partido no período: P1.", sources: [src("deputados/101/historico")] },
    ],
  },
};

export const compare: Schemas["CompareOut"] = {
  window, threshold, officials: [{ ...detailA, summary: null }, { ...detailA, official: summaryB, summary: null }],
};

export const parties: Schemas["PartiesOut"] = {
  window, threshold, house: "CAMARA",
  parties: [
    { party: "P1", member_ids: [1, 3], members_in_window: 2, members_at_start: 1, members_at_end: 2, membership_changed: true, members_with_sufficient_data: 1,
      aggregates: [{ key: "bills_authored", available: true, members_counted: 1, median: 3.6448, minimum: 3.6448, maximum: 3.6448 }] },
  ],
};
