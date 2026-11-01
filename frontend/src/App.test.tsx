import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { AppRoutes } from "./App";
import { text } from "./text/pt-BR";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  );
}

describe("routes", () => {
  it("renders the home page in Portuguese", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { level: 1, name: text.appName })).toBeInTheDocument();
  });

  it("renders a not-found page for unknown paths", () => {
    renderAt("/nao-existe");
    expect(screen.getByRole("heading", { name: text.notFoundTitle })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: text.backHome })).toHaveAttribute("href", "/");
  });
});
