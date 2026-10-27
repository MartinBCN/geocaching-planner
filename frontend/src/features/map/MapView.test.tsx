import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { createQueryClient } from "../../api/queryClient";
import { server } from "../../test/server";
import { MapView } from "./MapView";

type TestBounds = {
  getWest: () => number;
  getSouth: () => number;
  getEast: () => number;
  getNorth: () => number;
};

const viewBounds = {
  getWest: () => 4,
  getSouth: () => 51,
  getEast: () => 5,
  getNorth: () => 53,
};
const panBounds = {
  getWest: () => 4.1,
  getSouth: () => 51.1,
  getEast: () => 4.9,
  getNorth: () => 52.9,
};

const mapActions = vi.hoisted(() => ({
  easeTo: vi.fn(),
  fitBounds: vi.fn(),
  flyTo: vi.fn(),
  getClusterExpansionZoom: vi.fn(() => Promise.resolve(10)),
}));

vi.mock("react-map-gl/maplibre", async () => {
  const React = await import("react");
  const clusterSource = {
    getClusterExpansionZoom: mapActions.getClusterExpansionZoom,
  };
  const map = {
    getBounds: () => viewBounds,
    easeTo: mapActions.easeTo,
    fitBounds: mapActions.fitBounds,
    flyTo: mapActions.flyTo,
    getSource: () => clusterSource,
    queryRenderedFeatures: () => [],
  };
  const MockMap = React.forwardRef(
    (
      props: {
        children?: ReactNode;
        onLoad?: () => void;
        onMoveEnd?: (event: {
          target: { getBounds: () => TestBounds };
        }) => void;
        onClick?: (event: unknown) => void;
      },
      ref: React.Ref<{ getMap: () => typeof map }>,
    ) => {
      React.useImperativeHandle(ref, () => ({ getMap: () => map }), []);
      React.useEffect(() => props.onLoad?.(), [props.onLoad]);
      return (
        <div>
          <button
            type="button"
            onClick={() =>
              props.onMoveEnd?.({ target: { getBounds: () => panBounds } })
            }
          >
            Pan map
          </button>
          <button
            type="button"
            onClick={() =>
              props.onClick?.({
                features: [
                  {
                    properties: {
                      gcCode: "GC1ABC",
                      name: "Synthetic cache",
                      type: "Traditional",
                      container: "Small",
                      difficulty: 1.5,
                      terrain: 2,
                      found: false,
                      available: true,
                      archived: false,
                      corrected: true,
                    },
                    geometry: {
                      type: "Point",
                      coordinates: [4.1, 52.1],
                    },
                  },
                ],
                lngLat: { lat: 52.1, lng: 4.1 },
              })
            }
          >
            Click marker
          </button>
          <button
            type="button"
            onClick={() =>
              props.onClick?.({
                features: [
                  {
                    properties: { cluster: true, cluster_id: 7 },
                    geometry: { type: "Point", coordinates: [4, 52] },
                  },
                ],
                lngLat: { lat: 52, lng: 4 },
              })
            }
          >
            Click cluster
          </button>
          <button
            type="button"
            onClick={() =>
              props.onClick?.({
                features: [],
                lngLat: { lat: 52.2, lng: 4.2 },
              })
            }
          >
            Click empty map
          </button>
          {props.children}
        </div>
      );
    },
  );
  const Child = ({ children }: { children?: ReactNode }) => <>{children}</>;
  return {
    default: MockMap,
    Layer: () => null,
    Popup: Child,
    Source: Child,
  };
});

function renderMap(
  homeLocation: { lat: number; lon: number } | null = {
    lat: 52,
    lon: 4.3,
  },
  onLocationSelect?: (location: { lat: number; lon: number }) => void,
) {
  return render(
    <QueryClientProvider client={createQueryClient(false)}>
      <MemoryRouter>
        <MapView
          homeLocation={homeLocation}
          tileUrl="https://tiles.example/{z}/{x}/{y}.png"
          tileAttribution="Synthetic tile attribution"
          onLocationSelect={onLocationSelect}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("MapView", () => {
  it("debounces pan requests and displays a cache popup on marker click", async () => {
    mapActions.easeTo.mockClear();
    mapActions.fitBounds.mockClear();
    mapActions.flyTo.mockClear();
    mapActions.getClusterExpansionZoom.mockClear();
    const bboxes: string[] = [];
    server.use(
      http.get("*/api/v1/caches/markers", ({ request }) => {
        bboxes.push(new URL(request.url).searchParams.get("bbox") ?? "");
        return HttpResponse.json({
          items: [
            [
              "GC1ABC",
              "Synthetic cache",
              52.1,
              4.1,
              "Traditional",
              "Small",
              1.5,
              2,
              false,
              true,
              false,
              true,
            ],
          ],
          truncated: false,
          total: 1,
        });
      }),
    );
    renderMap();

    await waitFor(() => expect(bboxes).toHaveLength(1));
    fireEvent.click(screen.getByRole("button", { name: "Pan map" }));
    fireEvent.click(screen.getByRole("button", { name: "Pan map" }));
    await waitFor(() => expect(bboxes).toHaveLength(2), { timeout: 1500 });
    expect(bboxes[1]).toBe("4.10000,51.10000,4.90000,52.90000");

    fireEvent.click(screen.getByRole("button", { name: "Click marker" }));
    expect(screen.getByText("Synthetic cache")).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Cache details" }).getAttribute("href"),
    ).toBe("/caches/GC1ABC");

    fireEvent.click(screen.getByRole("button", { name: "Click cluster" }));
    await waitFor(() => expect(mapActions.easeTo).toHaveBeenCalledOnce());
    expect(mapActions.getClusterExpansionZoom).toHaveBeenCalledWith(7);
  });

  it("fits the initial map to all caches when there is no home location", async () => {
    mapActions.fitBounds.mockClear();
    const bboxes: string[] = [];
    server.use(
      http.get("*/api/v1/caches/markers", ({ request }) => {
        bboxes.push(new URL(request.url).searchParams.get("bbox") ?? "");
        return HttpResponse.json({
          items: [
            [
              "GC1ABC",
              "Cache one",
              52.1,
              4.1,
              "Traditional",
              "Small",
              1.5,
              2,
              false,
              true,
              false,
              false,
            ],
            [
              "GC2ABC",
              "Cache two",
              52.3,
              4.4,
              "Mystery",
              "Micro",
              2,
              2.5,
              true,
              true,
              false,
              false,
            ],
          ],
          truncated: false,
          total: 2,
        });
      }),
    );

    renderMap(null);

    await waitFor(() => expect(mapActions.fitBounds).toHaveBeenCalledOnce());
    expect(bboxes).toEqual(["-180,-85,180,85"]);
  });

  it("uses a blank map click to return a home-location coordinate", async () => {
    const onLocationSelect = vi.fn();
    renderMap(null, onLocationSelect);

    fireEvent.click(screen.getByRole("button", { name: "Click empty map" }));
    expect(onLocationSelect).toHaveBeenCalledWith({ lat: 52.2, lon: 4.2 });
  });

  it("reports marker API errors", async () => {
    server.use(
      http.get("*/api/v1/caches/markers", () =>
        HttpResponse.json(
          { title: "Marker service unavailable" },
          { status: 500 },
        ),
      ),
    );
    renderMap();

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Marker service unavailable",
    );
  });
});
