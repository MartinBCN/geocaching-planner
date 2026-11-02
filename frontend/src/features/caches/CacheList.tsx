import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { api } from "../../api/client";
import type { components, paths } from "../../api/schema";
import { useCacheFilters } from "../filters/CacheFilterContext";

type CacheSummary = components["schemas"]["CacheSummaryResponse"];
type ListQuery = NonNullable<
  paths["/api/v1/caches"]["get"]["parameters"]["query"]
>;
type Sort = NonNullable<ListQuery["sort"]>;

const PAGE_SIZE = 50;
const TABLE_COLUMNS = [
  { label: "GC code", sort: "gc_code" },
  { label: "Name", sort: "name" },
  { label: "Type" },
  { label: "D", sort: "difficulty" },
  { label: "T", sort: "terrain" },
  { label: "Size" },
  { label: "Distance", sort: "distance" },
] as const satisfies readonly (
  | { label: string; sort: Sort }
  | { label: string }
)[];
const VALID_SORTS = new Set<string>([
  "name",
  "-name",
  "gc_code",
  "-gc_code",
  "difficulty",
  "-difficulty",
  "terrain",
  "-terrain",
  "distance",
  "-distance",
  "placed_at",
  "-placed_at",
]);

function isSort(value: string): value is Sort {
  return VALID_SORTS.has(value);
}

function readPage(params: URLSearchParams): number {
  const parsed = Number(params.get("page"));
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1;
}

function readSort(params: URLSearchParams): Sort {
  const value = params.get("sort");
  return value && isSort(value) ? value : "gc_code";
}

function cacheTypeIcon(type: string): string {
  const initials = type
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2);
  return initials || "?";
}

async function fetchCaches(
  query: NonNullable<ListQuery>,
): Promise<components["schemas"]["CachePageResponse"]> {
  const { data, error } = await api.GET("/api/v1/caches", {
    params: { query },
  });
  if (!data) {
    throw new Error(error?.title ?? "Unable to load caches.");
  }
  return data;
}

export function CacheList({
  onHoverCache,
  hasHomeLocation,
}: {
  onHoverCache: (cache: CacheSummary | null) => void;
  hasHomeLocation: boolean;
}) {
  const { filters } = useCacheFilters();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const page = readPage(searchParams);
  const sort = readSort(searchParams);
  const effectiveSort =
    !hasHomeLocation && (sort === "distance" || sort === "-distance")
      ? "gc_code"
      : sort;
  const apiFilters =
    !hasHomeLocation && filters.max_distance_km !== undefined
      ? { ...filters, max_distance_km: undefined }
      : filters;
  const query = useMemo(
    () => ({ ...apiFilters, sort: effectiveSort, page, page_size: PAGE_SIZE }),
    [apiFilters, effectiveSort, page],
  );
  const cachesQuery = useQuery({
    queryKey: ["caches", query],
    queryFn: () => fetchCaches(query),
  });

  function updateListParams(patch: { page?: number; sort?: Sort }) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (patch.sort) {
          next.set("sort", patch.sort);
        }
        if (patch.page === undefined || patch.page === 1) {
          next.delete("page");
        } else {
          next.set("page", String(patch.page));
        }
        return next;
      },
      { replace: true },
    );
  }

  function toggleSort(field: Sort) {
    const nextSort = sort === field ? descendingSort(field) : field;
    updateListParams({ sort: nextSort, page: 1 });
  }

  function openCache(cache: CacheSummary) {
    navigate(`/caches/${encodeURIComponent(cache.gc_code)}`);
  }

  return (
    <section className="cache-list" aria-label="Cache list">
      {cachesQuery.isPending ? (
        <p role="status">Loading caches…</p>
      ) : cachesQuery.isError ? (
        <p role="alert">{cachesQuery.error.message}</p>
      ) : (
        <>
          <p className="cache-match-count" role="status">
            {cachesQuery.data.total} caches match
          </p>
          <div className="cache-table-scroll">
            <table>
              <thead>
                <tr>
                  {[...TABLE_COLUMNS, { label: "Found" }].map((column) => (
                    <th key={column.label} scope="col">
                      {"sort" in column ? (
                        <button
                          type="button"
                          aria-label={`Sort by ${column.label}`}
                          disabled={
                            column.sort === "distance" && !hasHomeLocation
                          }
                          title={
                            column.sort === "distance" && !hasHomeLocation
                              ? "Set a home location in Settings to sort by distance."
                              : undefined
                          }
                          onClick={() => toggleSort(column.sort)}
                        >
                          {column.label}
                          {sort === column.sort
                            ? " ↑"
                            : sort === `-${column.sort}`
                              ? " ↓"
                              : ""}
                        </button>
                      ) : (
                        column.label
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cachesQuery.data.items.map((cache) => (
                  <tr
                    key={cache.gc_code}
                    tabIndex={0}
                    aria-label={`Open cache ${cache.gc_code}, ${cache.name}`}
                    onClick={() => openCache(cache)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openCache(cache);
                      }
                    }}
                    onMouseEnter={() => onHoverCache(cache)}
                    onMouseLeave={() => onHoverCache(null)}
                    onFocus={() => onHoverCache(cache)}
                    onBlur={() => onHoverCache(null)}
                  >
                    <td>
                      <a
                        href={`/caches/${encodeURIComponent(cache.gc_code)}`}
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          openCache(cache);
                        }}
                      >
                        {cache.gc_code}
                      </a>
                    </td>
                    <td>{cache.name}</td>
                    <td>
                      <span
                        className="cache-type-icon"
                        role="img"
                        aria-label={cache.type}
                        title={cache.type}
                      >
                        {cacheTypeIcon(cache.type)}
                      </span>
                    </td>
                    <td>{cache.difficulty.toFixed(1)}</td>
                    <td>{cache.terrain.toFixed(1)}</td>
                    <td>{cache.container}</td>
                    <td>
                      {cache.distance_km === null
                        ? "—"
                        : `${cache.distance_km.toFixed(1)} km`}
                    </td>
                    <td>{cache.found_by_me ? "Found" : "Not found"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav className="cache-pagination" aria-label="Cache pages">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => updateListParams({ page: page - 1 })}
            >
              Previous
            </button>
            <span>
              Page {page} of{" "}
              {Math.max(1, Math.ceil(cachesQuery.data.total / PAGE_SIZE))}
            </span>
            <button
              type="button"
              disabled={page * PAGE_SIZE >= cachesQuery.data.total}
              onClick={() => updateListParams({ page: page + 1 })}
            >
              Next
            </button>
          </nav>
        </>
      )}
    </section>
  );
}

function descendingSort(field: Sort): Sort {
  switch (field) {
    case "name":
      return "-name";
    case "gc_code":
      return "-gc_code";
    case "difficulty":
      return "-difficulty";
    case "terrain":
      return "-terrain";
    case "distance":
      return "-distance";
    case "placed_at":
      return "-placed_at";
    default:
      return field;
  }
}
