import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter, useLocation, useSearchParams } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { createQueryClient } from "../../api/queryClient";
import type { components } from "../../api/schema";
import { server } from "../../test/server";
import { CacheFilterProvider } from "../filters/CacheFilterContext";
import { CacheBrowser } from "./CacheBrowser";

type Settings = components["schemas"]["SettingsResponse"];

const settings: Settings = {
  home_location: null,
  avg_speed_kmh: 18,
  corridor_m_default: 500,
  default_profile: "trekking",
  tile_url: "https://tiles.example/{z}/{x}/{y}.png",
  tile_attribution: "Synthetic attribution",
};

const cache: components["schemas"]["CacheSummaryResponse"] = {
  gc_code: "GC1ABC",
  name: "Synthetic cache",
  type: "Traditional",
  container: "Small",
  difficulty: 1.5,
  terrain: 2,
  distance_km: null,
  found_by_me: false,
  is_available: true,
  is_archived: false,
  has_corrected: false,
  lat: 52.1,
  lon: 4.1,
  placed_at: null,
};

const mapState = vi.hoisted(() => ({
  filters: "{}",
  highlighted: "",
}));

vi.mock("./MapView", () => ({
  MapView: (props: {
    filters?: Record<string, unknown>;
    highlightedCache?: { gcCode: string } | null;
  }) => {
    mapState.filters = JSON.stringify(props.filters ?? {});
    mapState.highlighted = props.highlightedCache?.gcCode ?? "";
    return (
      <div>
        <output data-testid="map-filters">{mapState.filters}</output>
        <output data-testid="highlighted-cache">{mapState.highlighted}</output>
      </div>
    );
  },
}));

function CurrentLocation() {
  const [params] = useSearchParams();
  const location = useLocation();
  return (
    <>
      <output data-testid="search-params">{params.toString()}</output>
      <output data-testid="current-path">{location.pathname}</output>
    </>
  );
}

function renderBrowser(path: string, browserSettings = settings) {
  return render(
    <QueryClientProvider client={createQueryClient(false)}>
      <MemoryRouter initialEntries={[path]}>
        <CacheFilterProvider>
          <CurrentLocation />
          <CacheBrowser settings={browserSettings} />
        </CacheFilterProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CacheBrowser", () => {
  it("shares URL-backed filters with the cache list and map", async () => {
    const listQueries: URLSearchParams[] = [];
    server.use(
      http.get("*/api/v1/caches", ({ request }) => {
        listQueries.push(new URL(request.url).searchParams);
        return HttpResponse.json({ items: [cache], total: 51 });
      }),
    );
    const user = userEvent.setup();
    renderBrowser("/");

    await screen.findByRole("row", {
      name: "Open cache GC1ABC, Synthetic cache",
    });
    await user.click(screen.getByRole("checkbox", { name: "Traditional" }));

    await waitFor(() => {
      expect(listQueries.at(-1)?.getAll("types")).toEqual(["Traditional"]);
      expect(
        JSON.parse(screen.getByTestId("map-filters").textContent ?? "{}"),
      ).toMatchObject({ types: ["Traditional"] });
    });
    expect(screen.getByTestId("search-params").textContent).toContain(
      "types=Traditional",
    );

    await user.selectOptions(screen.getByLabelText("Found status"), "found");
    await waitFor(() => {
      expect(listQueries.at(-1)?.get("found")).toBe("true");
      expect(
        JSON.parse(screen.getByTestId("map-filters").textContent ?? "{}"),
      ).toMatchObject({ found: true });
    });
  });

  it("restores filters from the URL and sends sort and paging to the API", async () => {
    const listQueries: URLSearchParams[] = [];
    server.use(
      http.get("*/api/v1/caches", ({ request }) => {
        listQueries.push(new URL(request.url).searchParams);
        return HttpResponse.json({ items: [cache], total: 51 });
      }),
    );
    const user = userEvent.setup();
    renderBrowser("/?types=Traditional&found=false&sort=-name&page=2");

    const traditionalFilter = (await screen.findByRole("checkbox", {
      name: "Traditional",
    })) as HTMLInputElement;
    expect(traditionalFilter.checked).toBe(true);
    expect(
      (screen.getByLabelText("Found status") as HTMLSelectElement).value,
    ).toBe("not-found");
    await waitFor(() => {
      expect(listQueries[0]?.get("sort")).toBe("-name");
      expect(listQueries[0]?.get("page")).toBe("2");
      expect(listQueries[0]?.get("page_size")).toBe("50");
    });

    await user.click(screen.getByRole("button", { name: "Sort by Name" }));
    await user.click(await screen.findByRole("button", { name: "Next" }));
    await waitFor(() => {
      expect(listQueries.at(-1)?.get("sort")).toBe("name");
      expect(listQueries.at(-1)?.get("page")).toBe("2");
      expect(listQueries.at(-1)?.get("page_size")).toBe("50");
    });
    await user.click(screen.getByRole("button", { name: "Sort by Name" }));
    await waitFor(() => {
      expect(listQueries.at(-1)?.get("sort")).toBe("-name");
      expect(listQueries.at(-1)?.get("page")).toBe("1");
    });
  });

  it("disables distance filtering without a home location", async () => {
    server.use(
      http.get("*/api/v1/caches", () =>
        HttpResponse.json({ items: [cache], total: 1 }),
      ),
    );
    renderBrowser("/");

    const distanceFilter = (await screen.findByLabelText(
      "Maximum distance from home (km)",
    )) as HTMLInputElement;
    expect(distanceFilter.disabled).toBe(true);
    const distanceSort = (await screen.findByRole("button", {
      name: "Sort by Distance",
    })) as HTMLButtonElement;
    expect(distanceSort.disabled).toBe(true);
    expect(
      screen.getByText(
        "Set a home location in Settings to use distance filtering.",
      ),
    ).toBeTruthy();
  });

  it("highlights the matching map marker while a list row is hovered", async () => {
    server.use(
      http.get("*/api/v1/caches", () =>
        HttpResponse.json({ items: [cache], total: 1 }),
      ),
    );
    renderBrowser("/");
    const row = await screen.findByRole("row", {
      name: "Open cache GC1ABC, Synthetic cache",
    });

    fireEvent.mouseEnter(row);
    await waitFor(() =>
      expect(screen.getByTestId("highlighted-cache").textContent).toBe(
        "GC1ABC",
      ),
    );
    fireEvent.mouseLeave(row);
    await waitFor(() =>
      expect(screen.getByTestId("highlighted-cache").textContent).toBe(""),
    );
  });

  it("sends size, range, status, archive, distance, and text filters together", async () => {
    const listQueries: URLSearchParams[] = [];
    server.use(
      http.get("*/api/v1/caches", ({ request }) => {
        listQueries.push(new URL(request.url).searchParams);
        return HttpResponse.json({ items: [cache], total: 1 });
      }),
    );
    const user = userEvent.setup();
    renderBrowser("/", {
      ...settings,
      home_location: { lat: 52.1, lon: 4.1 },
    });

    await screen.findByRole("row", {
      name: "Open cache GC1ABC, Synthetic cache",
    });
    await user.click(screen.getByRole("checkbox", { name: "Small" }));
    fireEvent.change(screen.getByLabelText("Minimum difficulty"), {
      target: { value: "2.5" },
    });
    fireEvent.change(screen.getByLabelText("Maximum difficulty"), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByLabelText("Minimum terrain"), {
      target: { value: "1.5" },
    });
    fireEvent.change(screen.getByLabelText("Maximum terrain"), {
      target: { value: "3" },
    });
    await user.selectOptions(screen.getByLabelText("Found status"), "found");
    await user.click(
      screen.getByRole("checkbox", { name: "Include archived" }),
    );
    await user.click(
      screen.getByRole("checkbox", { name: "Include disabled" }),
    );
    fireEvent.change(screen.getByLabelText("Maximum distance from home (km)"), {
      target: { value: "25" },
    });
    fireEvent.change(screen.getByLabelText("Search caches"), {
      target: { value: "river" },
    });

    await waitFor(() => {
      const params = listQueries.at(-1);
      expect(params?.getAll("containers")).toEqual(["Small"]);
      expect(params?.get("difficulty_min")).toBe("2.5");
      expect(params?.get("difficulty_max")).toBe("4");
      expect(params?.get("terrain_min")).toBe("1.5");
      expect(params?.get("terrain_max")).toBe("3");
      expect(params?.get("found")).toBe("true");
      expect(params?.get("include_archived")).toBe("true");
      expect(params?.get("include_disabled")).toBe("false");
      expect(params?.get("max_distance_km")).toBe("25");
      expect(params?.get("text")).toBe("river");
    });
  });

  it("clears a stale distance URL filter when the home location is unavailable", async () => {
    server.use(
      http.get("*/api/v1/caches", ({ request }) =>
        HttpResponse.json({
          items: [cache],
          total: new URL(request.url).searchParams.has("max_distance_km")
            ? 0
            : 1,
        }),
      ),
    );
    renderBrowser("/?max_distance_km=10&sort=distance&page=3");

    await waitFor(() => {
      const params = screen.getByTestId("search-params").textContent ?? "";
      expect(params).not.toContain("max_distance_km");
      expect(params).not.toContain("sort=distance");
      expect(params).not.toContain("page=3");
    });
  });

  it("resizes the split with the keyboard and opens a cache row", async () => {
    server.use(
      http.get("*/api/v1/caches", () =>
        HttpResponse.json({ items: [cache], total: 1 }),
      ),
    );
    const user = userEvent.setup();
    renderBrowser("/");
    const divider = await screen.findByRole("separator", {
      name: "Resize map and cache sidebar",
    });

    expect(divider.getAttribute("aria-valuenow")).toBe("48");
    fireEvent.keyDown(divider, { key: "ArrowRight" });
    expect(divider.getAttribute("aria-valuenow")).toBe("53");
    const workspace = divider.parentElement;
    if (!workspace) {
      throw new Error("The cache browser workspace is missing.");
    }
    vi.spyOn(workspace, "getBoundingClientRect").mockReturnValue({
      left: 0,
      width: 1000,
    } as DOMRect);
    const setPointerCapture = vi.fn();
    const hasPointerCapture = vi.fn(() => true);
    const releasePointerCapture = vi.fn();
    Object.defineProperties(divider, {
      setPointerCapture: { value: setPointerCapture },
      hasPointerCapture: { value: hasPointerCapture },
      releasePointerCapture: { value: releasePointerCapture },
    });
    fireEvent.pointerDown(divider, { pointerId: 7, clientX: 600 });
    expect(divider.getAttribute("aria-valuenow")).toBe("60");
    fireEvent.pointerMove(divider, { pointerId: 7, clientX: 700 });
    expect(divider.getAttribute("aria-valuenow")).toBe("70");
    fireEvent.pointerUp(divider, { pointerId: 7 });
    expect(setPointerCapture).toHaveBeenCalled();
    expect(hasPointerCapture).toHaveBeenCalled();
    expect(releasePointerCapture).toHaveBeenCalled();
    await user.click(screen.getByRole("link", { name: "GC1ABC" }));
    expect(screen.getByTestId("current-path").textContent).toBe(
      "/caches/GC1ABC",
    );
  });

  it("reports cache list request errors", async () => {
    server.use(
      http.get("*/api/v1/caches", () =>
        HttpResponse.json({ title: "Cache list unavailable" }, { status: 500 }),
      ),
    );
    renderBrowser("/");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Cache list unavailable");
  });
});
