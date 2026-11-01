import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderAt } from "../test/render";
import { text } from "../text/pt-BR";

/** Rule 3: every sourced value carries at least one link to an official https record. */
function expectSourcedValuesLinked(container: HTMLElement) {
  const values = within(container).queryAllByTestId("sourced-value");
  for (const value of values) {
    const links = within(value).queryAllByRole("link");
    const hrefs = links.map((a) => a.getAttribute("href") ?? "");
    if (value.textContent?.match(/\d/)) {
      expect(hrefs.length).toBeGreaterThan(0);
    }
    for (const href of hrefs) {
      expect(href).toMatch(/^https:\/\/([a-z0-9-]+\.)*(camara|senado)\.leg\.br\//);
    }
    for (const a of links) expect(a).toHaveAttribute("rel", "noopener noreferrer");
  }
  return values.length;
}

describe("officials page", () => {
  it("lists officials, flags insufficient data and links every number", async () => {
    const { container } = renderAt("/");
    expect(await screen.findByText("Pessoa A")).toBeInTheDocument();
    expect(screen.getByText(text.insufficientData)).toBeInTheDocument();
    expect(screen.getByText(text.officials.notInOffice(3))).toBeInTheDocument();
    expect(screen.getByTestId("window-summary")).toHaveTextContent("01/02/2023 a 01/11/2026");
    expect(expectSourcedValuesLinked(container)).toBeGreaterThan(0);
  });
});

describe("official page", () => {
  it("shows metrics with sources, leave days and not-available states", async () => {
    const { container } = renderAt("/parlamentar/1");
    expect(await screen.findByRole("heading", { level: 1, name: /Pessoa A/ })).toBeInTheDocument();
    expect(screen.getByText(/80,0%/)).toBeInTheDocument();
    expect(screen.getByText(text.metricValue.leaveDays("12"))).toBeInTheDocument();
    expect(screen.getByText(text.metricValue.perYear("3,6"))).toBeInTheDocument();
    expect(screen.getByText(text.metricValue.noneInPeriod)).toBeInTheDocument();
    expect(screen.getByText(text.notAvailableYet)).toBeInTheDocument();
    expect(screen.getByText(text.reasons.RESIGNATION!)).toBeInTheDocument();
    const summary = screen.getByTestId("summary");
    expect(within(summary).getByText(text.summary.template, { exact: false })).toBeInTheDocument();
    expect(within(summary).getAllByRole("listitem")).toHaveLength(2);
    expect(within(summary).getByRole("link", { name: text.summary.howItIsMade })).toHaveAttribute("href", "/metodologia#resumos");
    expect(expectSourcedValuesLinked(summary)).toBe(2);
    expectSourcedValuesLinked(container);
  });
});

describe("compare page", () => {
  it("asks for selections when fewer than two ids are given", async () => {
    renderAt("/comparar");
    expect(await screen.findByText(text.compare.hint)).toBeInTheDocument();
  });

  it("shows the window at the top and both officials side by side", async () => {
    const { container } = renderAt("/comparar?ids=1,2");
    const summary = await screen.findByTestId("window-summary");
    const table = screen.getByRole("table");
    expect(summary.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(table).getByText(/Pessoa B/)).toBeInTheDocument();
    expect(within(table).getByText(text.insufficientData)).toBeInTheDocument();
    expectSourcedValuesLinked(container);
  });
});

describe("parties page", () => {
  it("shows member counts and the membership-changed label", async () => {
    renderAt("/partidos");
    expect(await screen.findByText(text.parties.changed)).toBeInTheDocument();
    expect(screen.getByTestId("party-members")).toHaveAttribute("href", expect.stringContaining("/comparar?ids=1,3"));
  });
});
