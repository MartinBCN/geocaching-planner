import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { importApi } from "../../api/client";
import { createQueryClient } from "../../api/queryClient";
import type { components } from "../../api/schema";
import { ImportActivityContext } from "../../app/ImportActivityContext";
import { server } from "../../test/server";
import { ImportPage } from "./ImportPage";

type ImportRun = components["schemas"]["ImportRunResponse"];

const successfulRun: ImportRun = {
  id: 1,
  started_at: "2026-10-27T12:00:00Z",
  finished_at: "2026-10-27T12:00:01Z",
  source: "pq",
  filenames: ["pocket-query.gpx"],
  created: 3,
  updated: 0,
  unchanged: 0,
  waypoints: 2,
  errors: [],
};

afterEach(() => {
  vi.restoreAllMocks();
});

function renderImportPage() {
  const queryClient = createQueryClient(false);
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  const rendered = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/import"]}>
        <ImportActivityContext.Provider
          value={{ isImporting: false, setIsImporting: vi.fn() }}
        >
          <ImportPage />
        </ImportActivityContext.Provider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { ...rendered, invalidateQueries };
}

describe("ImportPage", () => {
  it("uploads multiple files, shows the summary, and invalidates caches and imports", async () => {
    const upload = vi.spyOn(importApi, "POST").mockImplementation(async () => ({
      data: successfulRun,
      response: new Response(null, { status: 201 }),
    }));
    const user = userEvent.setup();
    const { invalidateQueries } = renderImportPage();

    await user.upload(screen.getByLabelText("Choose files…"), [
      new File(["synthetic GPX"], "pocket-query.gpx"),
      new File(["synthetic ZIP"], "waypoints.zip"),
    ]);
    expect(screen.getByText("pocket-query.gpx")).toBeTruthy();
    expect(screen.getByText("waypoints.zip")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Import files" }));

    expect(
      await screen.findByRole("heading", { name: "Import summary" }),
    ).toBeTruthy();
    expect(
      screen.getByText(/3 created, 0 updated, 0 unchanged, 2 waypoints/),
    ).toBeTruthy();
    expect(screen.getByText(/pocket-query\.gpx/)).toBeTruthy();
    expect(upload).toHaveBeenCalledWith(
      "/api/v1/imports",
      expect.objectContaining({
        body: {
          files: expect.arrayContaining([expect.any(File), expect.any(File)]),
        },
      }),
    );
    await waitFor(() => {
      expect(invalidateQueries).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ["imports"] }),
      );
      expect(invalidateQueries).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ["caches"] }),
      );
    });
  });

  it("shows errors and warnings separately in summaries and history", async () => {
    const partialRun: ImportRun = {
      ...successfulRun,
      errors: [
        {
          severity: "error",
          file: "partial.gpx",
          gc_code: "GC0002B",
          line: 12,
          code: "invalid_entry",
          message: "Difficulty could not be read.",
        },
        {
          severity: "warning",
          file: "waypoints.gpx",
          gc_code: null,
          line: null,
          code: "orphan_waypoint",
          message: "Waypoint has no matching cache.",
        },
      ],
    };
    server.use(
      http.get("*/api/v1/imports", () => HttpResponse.json([partialRun])),
    );
    vi.spyOn(importApi, "POST").mockImplementation(async () => ({
      data: partialRun,
      response: new Response(null, { status: 201 }),
    }));
    const user = userEvent.setup();
    renderImportPage();

    await screen.findByText("pocket-query.gpx");
    const historySummary = screen.getAllByText(/pocket-query\.gpx/)[0];
    if (!historySummary) {
      throw new Error("Import history entry was not rendered.");
    }
    await user.click(historySummary);
    expect(
      await screen.findByText(/Waypoint has no matching cache/),
    ).toBeTruthy();
    await user.upload(
      screen.getByLabelText("Choose files…"),
      new File(["synthetic"], "partial.gpx"),
    );
    await user.click(screen.getByRole("button", { name: "Import files" }));
    const errorDetails = screen.getAllByText(
      (_, element) =>
        element?.tagName === "LI" &&
        element.textContent?.includes("Difficulty could not be read.") === true,
    );
    expect(errorDetails.length).toBeGreaterThan(0);
    expect(screen.getAllByText("Errors").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Warnings").length).toBeGreaterThan(0);
  });

  it("shows an actionable server error and an empty-history state", async () => {
    server.use(http.get("*/api/v1/imports", () => HttpResponse.json([])));
    vi.spyOn(importApi, "POST").mockRejectedValue(
      new Error("Import storage is unavailable."),
    );
    const user = userEvent.setup();
    renderImportPage();

    expect(await screen.findByText(/No imports yet/)).toBeTruthy();
    await user.upload(
      screen.getByLabelText("Choose files…"),
      new File(["synthetic"], "broken.gpx"),
    );
    await user.click(screen.getByRole("button", { name: "Import files" }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Import storage is unavailable.",
    );
  });

  it("disables controls and warns before leaving while an upload is pending", async () => {
    let completeRequest: (() => void) | undefined;
    vi.spyOn(importApi, "POST").mockImplementation(
      () =>
        new Promise((resolve) => {
          completeRequest = () =>
            resolve({
              data: successfulRun,
              response: new Response(null, { status: 201 }),
            });
        }),
    );
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={createQueryClient(false)}>
        <MemoryRouter initialEntries={["/import"]}>
          <ImportActivityContext.Provider
            value={{ isImporting: false, setIsImporting: vi.fn() }}
          >
            <ImportPage />
          </ImportActivityContext.Provider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await user.upload(
      screen.getByLabelText("Choose files…"),
      new File(["synthetic"], "pending.gpx"),
    );
    await user.click(screen.getByRole("button", { name: "Import files" }));
    expect(await screen.findByText(/Importing… pending.gpx/)).toBeTruthy();
    expect(
      (
        screen.getByRole("button", {
          name: "Choose files…",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      (
        screen.getByRole("button", {
          name: "Import files",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    const beforeUnload = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(beforeUnload);
    expect(beforeUnload.defaultPrevented).toBe(true);

    completeRequest?.();
    await screen.findByRole("heading", { name: "Import summary" });
  });

  it("offers a keyboard-focusable picker and drag-and-drop target", () => {
    renderImportPage();
    expect(screen.getByRole("button", { name: "Choose files…" })).toBeTruthy();
    const input = screen.getByLabelText("Choose files…");
    expect(input.hasAttribute("multiple")).toBe(true);
    expect(input.getAttribute("accept")).toBe(".gpx,.zip");
    expect(screen.getByText(/Drag files here/)).toBeTruthy();
  });
});
