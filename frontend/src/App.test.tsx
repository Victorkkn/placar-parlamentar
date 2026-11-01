import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderAt } from "./test/render";
import { text } from "./text/pt-BR";

describe("routes", () => {
  it("renders a not-found page for unknown paths", async () => {
    renderAt("/nao-existe");
    expect(await screen.findByRole("heading", { name: text.notFoundTitle })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: text.backHome })).toHaveAttribute("href", "/");
  });

  it("shows the snapshot date in pt-BR", async () => {
    renderAt("/metodologia");
    expect(await screen.findByText(text.snapshot("01/11/2026"))).toBeInTheDocument();
  });
});
