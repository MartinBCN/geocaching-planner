import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { HealthIndicator } from "../health/HealthIndicator";
import { MapView } from "./MapView";

type SettingsResponse = components["schemas"]["SettingsResponse"];

async function fetchSettings(): Promise<SettingsResponse> {
  const { data, error } = await api.GET("/api/v1/settings");
  if (!data) {
    throw new Error(error?.title ?? "Unable to load map settings.");
  }
  return data;
}

export function MapPage() {
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  if (settingsQuery.isPending) {
    return <p role="status">Loading map settings…</p>;
  }
  if (settingsQuery.isError) {
    return <p role="alert">{settingsQuery.error.message}</p>;
  }

  return (
    <section className="map-page" aria-labelledby="map-page-title">
      <h1 className="visually-hidden" id="map-page-title">
        Map
      </h1>
      <MapView
        homeLocation={settingsQuery.data.home_location}
        tileUrl={settingsQuery.data.tile_url}
        tileAttribution={settingsQuery.data.tile_attribution}
      />
      <div className="map-health">
        <HealthIndicator />
      </div>
    </section>
  );
}
