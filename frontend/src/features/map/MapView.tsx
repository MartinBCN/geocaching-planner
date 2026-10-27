import { useQuery } from "@tanstack/react-query";
import type { GeoJSONSource } from "maplibre-gl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import MapGL, {
  Layer,
  type MapLayerMouseEvent,
  type MapRef,
  Popup,
  Source,
} from "react-map-gl/maplibre";
import { Link } from "react-router";
import { api } from "../../api/client";
import type { components, paths } from "../../api/schema";
import {
  markerColorExpression,
  markerOpacityExpression,
  markerStrokeColorExpression,
  markerStrokeWidthExpression,
} from "./styles";

type SettingsResponse = components["schemas"]["SettingsResponse"];
type Coordinates = NonNullable<SettingsResponse["home_location"]>;
type Marker = components["schemas"]["CacheMarkersResponse"]["items"][number];
type MarkerQuery =
  paths["/api/v1/caches/markers"]["get"]["parameters"]["query"];
type MarkerFilters = Omit<MarkerQuery, "bbox">;
type Bounds = {
  getWest(): number;
  getSouth(): number;
  getEast(): number;
  getNorth(): number;
};
type MarkerProperties = {
  gcCode: string;
  name: string;
  type: string;
  container: string;
  difficulty: number;
  terrain: number;
  found: boolean;
  available: boolean;
  archived: boolean;
  corrected: boolean;
};

interface MapViewProps {
  homeLocation: Coordinates | null;
  tileUrl: string;
  tileAttribution: string;
  filters?: MarkerFilters;
  onLocationSelect?: (location: Coordinates) => void;
  className?: string;
}

const WORLD_BBOX = "-180,-85,180,85";
const NETHERLANDS = { longitude: 5.3, latitude: 52.1, zoom: 7 };

function boundsToBbox(bounds: Bounds): string {
  const west = bounds.getWest();
  const south = bounds.getSouth();
  const east = bounds.getEast();
  const north = bounds.getNorth();

  if (west > east) {
    return WORLD_BBOX;
  }
  return [west, south, east, north].map((value) => value.toFixed(5)).join(",");
}

async function fetchMarkers(
  bbox: string,
  filters: MarkerFilters,
): Promise<components["schemas"]["CacheMarkersResponse"]> {
  const { data, error } = await api.GET("/api/v1/caches/markers", {
    params: { query: { ...filters, bbox } },
  });
  if (!data) {
    throw new Error(error?.title ?? "Unable to load cache markers.");
  }
  return { ...data, items: data.items.map(parseMarker) };
}

function parseMarker(value: unknown): Marker {
  if (
    !Array.isArray(value) ||
    value.length !== 12 ||
    typeof value[0] !== "string" ||
    typeof value[1] !== "string" ||
    typeof value[2] !== "number" ||
    !Number.isFinite(value[2]) ||
    typeof value[3] !== "number" ||
    !Number.isFinite(value[3]) ||
    typeof value[4] !== "string" ||
    typeof value[5] !== "string" ||
    typeof value[6] !== "number" ||
    !Number.isFinite(value[6]) ||
    typeof value[7] !== "number" ||
    !Number.isFinite(value[7]) ||
    typeof value[8] !== "boolean" ||
    typeof value[9] !== "boolean" ||
    typeof value[10] !== "boolean" ||
    typeof value[11] !== "boolean"
  ) {
    throw new Error("The cache marker response has an invalid item.");
  }
  return [
    value[0],
    value[1],
    value[2],
    value[3],
    value[4],
    value[5],
    value[6],
    value[7],
    value[8],
    value[9],
    value[10],
    value[11],
  ];
}

function toFeatureCollection(markers: Marker[]) {
  return {
    type: "FeatureCollection" as const,
    features: markers.map(
      ([
        gcCode,
        name,
        latitude,
        longitude,
        type,
        container,
        difficulty,
        terrain,
        found,
        available,
        archived,
        corrected,
      ]) => ({
        type: "Feature" as const,
        id: gcCode,
        geometry: {
          type: "Point" as const,
          coordinates: [longitude, latitude] as [number, number],
        },
        properties: {
          gcCode,
          name,
          type,
          container,
          difficulty,
          terrain,
          found,
          available,
          archived,
          corrected,
        } satisfies MarkerProperties,
      }),
    ),
  };
}

export function MapView({
  homeLocation,
  tileUrl,
  tileAttribution,
  filters = {},
  onLocationSelect,
  className,
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null);
  const initialFitApplied = useRef(false);
  const [rawBbox, setRawBbox] = useState<string>();
  const [bbox, setBbox] = useState<string>();
  const [selectedMarker, setSelectedMarker] = useState<
    (MarkerProperties & { latitude: number; longitude: number }) | null
  >(null);
  const [mapError, setMapError] = useState<string | null>(null);
  const [readyMarkerData, setReadyMarkerData] = useState<
    components["schemas"]["CacheMarkersResponse"] | null
  >(null);
  const mapFilters = useMemo(() => filters, [filters]);
  const initialMarkersQuery = useQuery({
    queryKey: ["cache-markers", "initial-bounds", mapFilters],
    queryFn: () => fetchMarkers(WORLD_BBOX, mapFilters),
    enabled: homeLocation === null,
    staleTime: 5 * 60 * 1000,
  });
  const markersQuery = useQuery({
    queryKey: ["cache-markers", bbox, mapFilters],
    queryFn: () => fetchMarkers(bbox ?? WORLD_BBOX, mapFilters),
    enabled: bbox !== undefined,
    staleTime: 15 * 1000,
  });

  const features = useMemo(
    () => toFeatureCollection(markersQuery.data?.items ?? []),
    [markersQuery.data?.items],
  );
  const rasterStyle = useMemo(
    () => ({
      version: 8 as const,
      sources: {
        cycle: {
          type: "raster" as const,
          tiles: [tileUrl.replace("{s}", "a")],
          tileSize: 256,
          attribution: tileAttribution,
        },
      },
      layers: [{ id: "cycle", type: "raster" as const, source: "cycle" }],
    }),
    [tileAttribution, tileUrl],
  );

  const updateBbox = useCallback((bounds: Bounds) => {
    setRawBbox(boundsToBbox(bounds));
  }, []);

  useEffect(() => {
    if (!rawBbox) {
      return;
    }
    const timer = window.setTimeout(() => setBbox(rawBbox), 300);
    return () => window.clearTimeout(timer);
  }, [rawBbox]);

  const handleSourceData = useCallback(
    (event: { sourceId?: string; isSourceLoaded?: boolean }) => {
      if (
        event.sourceId === "cache-markers" &&
        event.isSourceLoaded &&
        markersQuery.data
      ) {
        setReadyMarkerData(markersQuery.data);
      }
    },
    [markersQuery.data],
  );
  const markerSourceReady =
    markersQuery.data !== undefined && readyMarkerData === markersQuery.data;

  const fitInitialMarkers = useCallback(() => {
    const map = mapRef.current?.getMap();
    const data = initialMarkersQuery.data;
    if (!map || !data || initialFitApplied.current) {
      return;
    }
    initialFitApplied.current = true;
    const coordinates: [number, number][] = data.items.map((item) => [
      item[3],
      item[2],
    ]);
    if (coordinates.length === 0) {
      updateBbox(map.getBounds());
      return;
    }
    if (coordinates.length === 1) {
      const coordinate = coordinates[0];
      if (coordinate) {
        map.flyTo({ center: coordinate, zoom: 12 });
      }
      return;
    }
    const longitudes = coordinates.map(([longitude]) => longitude);
    const latitudes = coordinates.map(([, latitude]) => latitude);
    map.fitBounds(
      [
        [Math.min(...longitudes), Math.min(...latitudes)],
        [Math.max(...longitudes), Math.max(...latitudes)],
      ],
      { padding: 48, maxZoom: 12 },
    );
  }, [initialMarkersQuery.data, updateBbox]);

  useEffect(() => {
    if (homeLocation === null && initialMarkersQuery.isFetched) {
      fitInitialMarkers();
    }
  }, [fitInitialMarkers, homeLocation, initialMarkersQuery.isFetched]);

  const handleMapLoad = useCallback(() => {
    const bounds = mapRef.current?.getMap().getBounds();
    if (homeLocation !== null && bounds) {
      updateBbox(bounds);
    } else if (homeLocation === null && initialMarkersQuery.isFetched) {
      fitInitialMarkers();
    }
  }, [
    fitInitialMarkers,
    homeLocation,
    initialMarkersQuery.isFetched,
    updateBbox,
  ]);

  const handleMapClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const map = mapRef.current?.getMap();
      const feature =
        event.features?.[0] ??
        map?.queryRenderedFeatures(event.point, {
          layers: ["cache-clusters", "cache-points"],
        })[0];
      if (!feature) {
        setSelectedMarker(null);
        onLocationSelect?.({
          lat: event.lngLat.lat,
          lon: event.lngLat.lng,
        });
        return;
      }

      const properties = feature.properties;
      if (properties?.cluster === true || properties?.cluster === 1) {
        const source = mapRef.current?.getMap().getSource("cache-markers") as
          | GeoJSONSource
          | undefined;
        const clusterId = Number(properties.cluster_id);
        if (source && Number.isFinite(clusterId)) {
          void source
            .getClusterExpansionZoom(clusterId)
            .then((zoom) => {
              mapRef.current?.getMap().easeTo({
                center: event.lngLat,
                zoom,
              });
            })
            .catch((error: unknown) => {
              setMapError(
                error instanceof Error
                  ? error.message
                  : "Unable to expand this cache cluster.",
              );
            });
        }
        return;
      }

      const geometry = feature.geometry;
      if (geometry.type !== "Point") {
        return;
      }
      const coordinates = geometry.coordinates;
      setSelectedMarker({
        gcCode: String(properties?.gcCode ?? ""),
        name: String(properties?.name ?? ""),
        type: String(properties?.type ?? ""),
        container: String(properties?.container ?? ""),
        difficulty: Number(properties?.difficulty),
        terrain: Number(properties?.terrain),
        found: Boolean(properties?.found),
        available: Boolean(properties?.available),
        archived: Boolean(properties?.archived),
        corrected: Boolean(properties?.corrected),
        longitude: coordinates[0],
        latitude: coordinates[1],
      });
    },
    [onLocationSelect],
  );

  const initialViewState = homeLocation
    ? {
        longitude: homeLocation.lon,
        latitude: homeLocation.lat,
        zoom: 15,
      }
    : NETHERLANDS;

  return (
    <div
      className={`map-view${className ? ` ${className}` : ""}`}
      data-testid="cache-map"
      data-marker-source-ready={markerSourceReady}
    >
      <MapGL
        ref={mapRef}
        aria-label="Cache map"
        initialViewState={initialViewState}
        mapStyle={rasterStyle}
        attributionControl={false}
        onLoad={handleMapLoad}
        onMoveEnd={(event) => updateBbox(event.target.getBounds())}
        onClick={handleMapClick}
        onSourceData={handleSourceData}
        interactiveLayerIds={["cache-clusters", "cache-points"]}
        style={{ width: "100%", height: "100%" }}
      >
        {markersQuery.data && (
          <Source
            id="cache-markers"
            type="geojson"
            data={features}
            cluster
            clusterMaxZoom={14}
            clusterRadius={50}
          >
            <Layer
              id="cache-clusters"
              type="circle"
              filter={["has", "point_count"]}
              paint={{
                "circle-color": "#1d4ed8",
                "circle-radius": [
                  "step",
                  ["get", "point_count"],
                  16,
                  10,
                  20,
                  50,
                  25,
                ],
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 2,
              }}
            />
            <Layer
              id="cache-cluster-count"
              type="symbol"
              filter={["has", "point_count"]}
              layout={{
                "text-field": ["get", "point_count_abbreviated"],
                "text-size": 12,
              }}
              paint={{ "text-color": "#ffffff" }}
            />
            <Layer
              id="cache-points"
              type="circle"
              filter={["!", ["has", "point_count"]]}
              paint={{
                "circle-color": markerColorExpression,
                "circle-opacity": markerOpacityExpression,
                "circle-radius": ["case", ["==", ["get", "found"], true], 7, 6],
                "circle-stroke-color": markerStrokeColorExpression,
                "circle-stroke-width": markerStrokeWidthExpression,
              }}
            />
          </Source>
        )}
        {selectedMarker && (
          <Popup
            longitude={selectedMarker.longitude}
            latitude={selectedMarker.latitude}
            closeButton
            closeOnClick={false}
            onClose={() => setSelectedMarker(null)}
          >
            <section aria-label={`Cache ${selectedMarker.gcCode}`}>
              <strong>{selectedMarker.name}</strong>
              <p>{selectedMarker.gcCode}</p>
              <p>
                {selectedMarker.type} · {selectedMarker.container}
              </p>
              <p>
                D {selectedMarker.difficulty} · T {selectedMarker.terrain}
              </p>
              <Link to={`/caches/${encodeURIComponent(selectedMarker.gcCode)}`}>
                Cache details
              </Link>
            </section>
          </Popup>
        )}
      </MapGL>

      {tileAttribution && (
        <aside className="map-attribution" aria-label="Map attribution">
          {tileAttribution}
        </aside>
      )}
      {markersQuery.data?.truncated && (
        <p className="map-banner" role="status">
          Zoom in to see all caches
        </p>
      )}
      {(markersQuery.isError || mapError) && (
        <p className="map-error" role="alert">
          {mapError ??
            markersQuery.error?.message ??
            "Unable to load cache markers."}
        </p>
      )}
      {markersQuery.isPending && bbox && (
        <p className="map-loading" role="status">
          Loading caches…
        </p>
      )}
      {initialMarkersQuery.isError && (
        <p className="map-error" role="alert">
          {initialMarkersQuery.error.message}
        </p>
      )}
    </div>
  );
}
