import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { createQueryClient } from "../api/queryClient";
import { server } from "../test/server";
import { AppRoutes } from "./AppRoutes";

function renderAt(path: string) {
  return render(
    <QueryClientProvider client={createQueryClient(false)}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppRoutes", () => {
  it("renders the nav in the order Map, Import, Routes, Settings", () => {
    renderAt("/import");
    const links = screen.getAllByRole("link").map((el) => el.textContent);
    expect(links.slice(0, 4)).toEqual(["Map", "Import", "Routes", "Settings"]);
  });

  it.each([
    ["/import", "Import"],
    ["/routes", "Routes"],
    ["/routes/42", "Route"],
    ["/caches/GC1ABC", "Cache"],
    ["/settings", "Settings"],
  ])("renders the %s page with its title", async (path, title) => {
    renderAt(path);
    expect((await screen.findByRole("heading", { level: 1 })).textContent).toBe(
      title,
    );
  });

  it("renders the map page with the health indicator", async () => {
    server.use(
      http.get("*/api/v1/health", () =>
        HttpResponse.json({ status: "ok", version: "t", db: "ok" }),
      ),
    );
    renderAt("/");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Map");
    expect(await screen.findByText("Backend: ok")).toBeTruthy();
  });

  it("renders the not-found page with a link back to the map", () => {
    renderAt("/does-not-exist");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
      "Page not found",
    );
    expect(
      screen
        .getByRole("link", { name: "Back to the map" })
        .getAttribute("href"),
    ).toBe("/");
  });
});
