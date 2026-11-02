import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import type { components } from "../../api/schema";
import { CacheList } from "../caches/CacheList";
import { useCacheFilters } from "../filters/CacheFilterContext";
import { FilterPanel } from "../filters/FilterPanel";
import { MapView } from "./MapView";

type SettingsResponse = components["schemas"]["SettingsResponse"];
export function CacheBrowser({ settings }: { settings: SettingsResponse }) {
  const { filters } = useCacheFilters();
  const [searchParams, setSearchParams] = useSearchParams();
  const [mapWidth, setMapWidth] = useState(48);
  const [highlightedCache, setHighlightedCache] = useState<
    components["schemas"]["CacheSummaryResponse"] | null
  >(null);
  const workspaceRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sort = searchParams.get("sort");
    const hasDistanceSort = sort === "distance" || sort === "-distance";
    if (
      settings.home_location === null &&
      (filters.max_distance_km !== undefined || hasDistanceSort)
    ) {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.delete("max_distance_km");
          if (hasDistanceSort) {
            next.delete("sort");
          }
          next.delete("page");
          return next;
        },
        { replace: true },
      );
    }
  }, [
    filters.max_distance_km,
    searchParams,
    setSearchParams,
    settings.home_location,
  ]);
  const mapFilters =
    settings.home_location === null && filters.max_distance_km !== undefined
      ? { ...filters, max_distance_km: undefined }
      : filters;

  function updateSplit(clientX: number) {
    const bounds = workspaceRef.current?.getBoundingClientRect();
    if (!bounds || bounds.width <= 0) {
      return;
    }
    const percent = ((clientX - bounds.left) / bounds.width) * 100;
    setMapWidth(Math.max(30, Math.min(70, percent)));
  }

  function handleDividerKeyDown(event: React.KeyboardEvent<HTMLHRElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 5 : -5;
    setMapWidth((width) => Math.max(30, Math.min(70, width + direction)));
  }

  return (
    <div
      className="cache-browser"
      ref={workspaceRef}
      style={{
        gridTemplateColumns: `minmax(0, ${mapWidth}fr) 8px minmax(24rem, ${100 - mapWidth}fr)`,
      }}
    >
      <section className="cache-map-pane" aria-label="Cache map panel">
        <MapView
          homeLocation={settings.home_location}
          tileUrl={settings.tile_url}
          tileAttribution={settings.tile_attribution}
          filters={mapFilters}
          highlightedCache={
            highlightedCache
              ? {
                  gcCode: highlightedCache.gc_code,
                  latitude: highlightedCache.lat,
                  longitude: highlightedCache.lon,
                }
              : null
          }
        />
      </section>
      <hr
        className="cache-browser-divider"
        aria-label="Resize map and cache sidebar"
        aria-orientation="vertical"
        aria-valuemin={30}
        aria-valuemax={70}
        aria-valuenow={Math.round(mapWidth)}
        tabIndex={0}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId);
          updateSplit(event.clientX);
        }}
        onPointerMove={(event) => {
          if (event.currentTarget.hasPointerCapture(event.pointerId)) {
            updateSplit(event.clientX);
          }
        }}
        onPointerUp={(event) => {
          if (event.currentTarget.hasPointerCapture(event.pointerId)) {
            event.currentTarget.releasePointerCapture(event.pointerId);
          }
        }}
        onKeyDown={handleDividerKeyDown}
      />
      <aside className="cache-sidebar" aria-label="Cache filters and results">
        <FilterPanel homeLocation={settings.home_location} />
        <CacheList
          onHoverCache={setHighlightedCache}
          hasHomeLocation={settings.home_location !== null}
        />
      </aside>
    </div>
  );
}
