import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { importApi } from "../api/client";
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

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("AppRoutes", () => {
  it("renders the nav in the order Map, Import, Routes, Settings", () => {
    renderAt("/import");
    const links = screen.getAllByRole("link").map((el) => el.textContent);
    expect(links.slice(0, 4)).toEqual(["Map", "Import", "Routes", "Settings"]);
  });

  it.each([
    ["/import", "Import Pocket Queries"],
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
    expect((await screen.findByRole("heading", { level: 1 })).textContent).toBe(
      "Map",
    );
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

  it("warns before navigating away during an active import", async () => {
    let finishImport: (() => void) | undefined;
    vi.spyOn(importApi, "POST").mockImplementation(
      () =>
        new Promise((resolve) => {
          finishImport = () =>
            resolve({
              data: {
                id: 1,
                started_at: "2026-10-27T12:00:00Z",
                finished_at: "2026-10-27T12:00:01Z",
                source: "pq",
                filenames: ["pending.gpx"],
                created: 0,
                updated: 0,
                unchanged: 0,
                waypoints: 0,
                errors: [],
              },
              response: new Response(null, { status: 201 }),
            });
        }),
    );
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);
    const user = userEvent.setup();
    renderAt("/import");

    await user.upload(
      screen.getByLabelText("Choose files…"),
      new File(["synthetic"], "pending.gpx"),
    );
    await user.click(screen.getByRole("button", { name: "Import files" }));
    await screen.findByText(/Importing… pending\.gpx/);
    await user.click(screen.getByRole("link", { name: "Routes" }));

    expect(confirm).toHaveBeenCalledOnce();
    expect(
      await screen.findByRole("heading", { name: "Import Pocket Queries" }),
    ).toBeTruthy();
    finishImport?.();
    expect(
      await screen.findByRole("heading", { name: "Import summary" }),
    ).toBeTruthy();
  });
});
