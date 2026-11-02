import { createContext, type ReactNode, useContext, useMemo } from "react";
import { useSearchParams } from "react-router";
import type { components, paths } from "../../api/schema";

type MarkerQuery = NonNullable<
  paths["/api/v1/caches/markers"]["get"]["parameters"]["query"]
>;
export type CacheFilters = Omit<MarkerQuery, "bbox">;
type CacheType = components["schemas"]["CacheType"];
type ContainerSize = components["schemas"]["ContainerSize"];
type FilterContextValue = {
  filters: CacheFilters;
  updateFilters: (patch: Partial<CacheFilters>) => void;
};

const CacheFilterContext = createContext<FilterContextValue | null>(null);

const CACHE_TYPES: CacheType[] = [
  "Traditional",
  "Multi",
  "Mystery",
  "Letterbox",
  "EarthCache",
  "Wherigo",
  "Virtual",
  "Event",
  "CITO",
  "Mega",
  "Giga",
  "Webcam",
  "Lab",
  "Other",
];
const CONTAINER_SIZES: ContainerSize[] = [
  "Micro",
  "Small",
  "Regular",
  "Large",
  "Virtual",
  "Other",
  "Not chosen",
];

function isCacheType(value: string): value is CacheType {
  return CACHE_TYPES.includes(value as CacheType);
}

function isContainerSize(value: string): value is ContainerSize {
  return CONTAINER_SIZES.includes(value as ContainerSize);
}

function numberParam(
  params: URLSearchParams,
  name: string,
): number | undefined {
  const value = params.get(name);
  if (value === null || value.trim() === "") {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function booleanParam(
  params: URLSearchParams,
  name: string,
): boolean | undefined {
  const value = params.get(name);
  return value === "true" ? true : value === "false" ? false : undefined;
}

function readFilters(params: URLSearchParams): CacheFilters {
  const types = params.getAll("types").filter(isCacheType);
  const containers = params.getAll("containers").filter(isContainerSize);
  const text = params.get("text")?.trim();
  const found = booleanParam(params, "found");
  const includeArchived = booleanParam(params, "include_archived");
  const includeDisabled = booleanParam(params, "include_disabled");
  const difficultyMin = numberParam(params, "difficulty_min");
  const difficultyMax = numberParam(params, "difficulty_max");
  const terrainMin = numberParam(params, "terrain_min");
  const terrainMax = numberParam(params, "terrain_max");
  const maxDistance = numberParam(params, "max_distance_km");
  return {
    ...(types.length > 0 ? { types } : {}),
    ...(containers.length > 0 ? { containers } : {}),
    ...(difficultyMin !== undefined ? { difficulty_min: difficultyMin } : {}),
    ...(difficultyMax !== undefined ? { difficulty_max: difficultyMax } : {}),
    ...(terrainMin !== undefined ? { terrain_min: terrainMin } : {}),
    ...(terrainMax !== undefined ? { terrain_max: terrainMax } : {}),
    ...(found !== undefined ? { found } : {}),
    include_archived: includeArchived ?? false,
    include_disabled: includeDisabled ?? true,
    ...(maxDistance !== undefined ? { max_distance_km: maxDistance } : {}),
    ...(text ? { text } : {}),
  };
}

function updateSearchParams(
  params: URLSearchParams,
  patch: Partial<CacheFilters>,
): URLSearchParams {
  const next = new URLSearchParams(params);
  for (const [key, value] of Object.entries(patch)) {
    next.delete(key);
    if (value === undefined || value === null) {
      continue;
    }
    if (key === "include_archived" && value === false) {
      continue;
    }
    if (key === "include_disabled" && value === true) {
      continue;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        next.append(key, item);
      }
    } else {
      next.set(key, String(value));
    }
  }
  next.delete("page");
  return next;
}

export function CacheFilterProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => readFilters(searchParams), [searchParams]);
  const contextValue = useMemo(
    () => ({
      filters,
      updateFilters: (patch: Partial<CacheFilters>) =>
        setSearchParams((current) => updateSearchParams(current, patch), {
          replace: true,
        }),
    }),
    [filters, setSearchParams],
  );
  return (
    <CacheFilterContext.Provider value={contextValue}>
      {children}
    </CacheFilterContext.Provider>
  );
}

export function useCacheFilters(): FilterContextValue {
  const context = useContext(CacheFilterContext);
  if (!context) {
    throw new Error("useCacheFilters must be used within CacheFilterProvider.");
  }
  return context;
}

export { CACHE_TYPES, CONTAINER_SIZES };
