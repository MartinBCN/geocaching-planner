import type { components } from "../../api/schema";
import {
  CACHE_TYPES,
  type CacheFilters,
  CONTAINER_SIZES,
  useCacheFilters,
} from "./CacheFilterContext";

type Coordinates = components["schemas"]["CoordinatesModel"] | null;
type RangePatch = Partial<
  Pick<
    CacheFilters,
    "difficulty_min" | "difficulty_max" | "terrain_min" | "terrain_max"
  >
>;

function RangeControl({
  label,
  minName,
  maxName,
  minValue,
  maxValue,
  update,
}: {
  label: string;
  minName: "difficulty_min" | "terrain_min";
  maxName: "difficulty_max" | "terrain_max";
  minValue: number | null | undefined;
  maxValue: number | null | undefined;
  update: (patch: RangePatch) => void;
}) {
  const min = minValue ?? 1;
  const max = maxValue ?? 5;
  return (
    <fieldset className="filter-range">
      <legend>{label}</legend>
      <label>
        Minimum {label.toLowerCase()} ({min.toFixed(1)})
        <input
          aria-label={`Minimum ${label.toLowerCase()}`}
          type="range"
          min="1"
          max={max}
          step="0.5"
          value={min}
          onChange={(event) =>
            update({ [minName]: Number(event.currentTarget.value) })
          }
        />
      </label>
      <label>
        Maximum {label.toLowerCase()} ({max.toFixed(1)})
        <input
          aria-label={`Maximum ${label.toLowerCase()}`}
          type="range"
          min={min}
          max="5"
          step="0.5"
          value={max}
          onChange={(event) =>
            update({ [maxName]: Number(event.currentTarget.value) })
          }
        />
      </label>
    </fieldset>
  );
}

export function FilterPanel({ homeLocation }: { homeLocation: Coordinates }) {
  const { filters, updateFilters } = useCacheFilters();
  const selectedTypes = filters.types ?? [];
  const selectedContainers = filters.containers ?? [];

  function updateSelection<T extends string>(
    current: T[],
    value: T,
    checked: boolean,
    update: (values: T[]) => void,
  ) {
    update(
      checked ? [...current, value] : current.filter((item) => item !== value),
    );
  }

  return (
    <form
      className="cache-filters"
      aria-label="Cache filters"
      onSubmit={(event) => event.preventDefault()}
    >
      <fieldset>
        <legend>Cache type</legend>
        <div className="filter-options">
          {CACHE_TYPES.map((type) => (
            <label key={type}>
              <input
                type="checkbox"
                checked={selectedTypes.includes(type)}
                onChange={(event) =>
                  updateSelection(
                    selectedTypes,
                    type,
                    event.currentTarget.checked,
                    (types) =>
                      updateFilters({
                        types: types.length > 0 ? types : undefined,
                      }),
                  )
                }
              />
              {type}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend>Container size</legend>
        <div className="filter-options">
          {CONTAINER_SIZES.map((size) => (
            <label key={size}>
              <input
                type="checkbox"
                checked={selectedContainers.includes(size)}
                onChange={(event) =>
                  updateSelection(
                    selectedContainers,
                    size,
                    event.currentTarget.checked,
                    (containers) =>
                      updateFilters({
                        containers:
                          containers.length > 0 ? containers : undefined,
                      }),
                  )
                }
              />
              {size}
            </label>
          ))}
        </div>
      </fieldset>

      <RangeControl
        label="Difficulty"
        minName="difficulty_min"
        maxName="difficulty_max"
        minValue={filters.difficulty_min ?? undefined}
        maxValue={filters.difficulty_max ?? undefined}
        update={updateFilters}
      />
      <RangeControl
        label="Terrain"
        minName="terrain_min"
        maxName="terrain_max"
        minValue={filters.terrain_min ?? undefined}
        maxValue={filters.terrain_max ?? undefined}
        update={updateFilters}
      />

      <label>
        Found status
        <select
          value={
            filters.found === undefined
              ? "all"
              : filters.found
                ? "found"
                : "not-found"
          }
          onChange={(event) =>
            updateFilters({
              found:
                event.currentTarget.value === "all"
                  ? undefined
                  : event.currentTarget.value === "found",
            })
          }
        >
          <option value="all">All caches</option>
          <option value="found">Found</option>
          <option value="not-found">Not found</option>
        </select>
      </label>

      <label>
        <input
          type="checkbox"
          checked={filters.include_archived ?? false}
          onChange={(event) =>
            updateFilters({ include_archived: event.currentTarget.checked })
          }
        />
        Include archived
      </label>
      <label>
        <input
          type="checkbox"
          checked={filters.include_disabled ?? true}
          onChange={(event) =>
            updateFilters({ include_disabled: event.currentTarget.checked })
          }
        />
        Include disabled
      </label>

      <label>
        Maximum distance from home (km)
        <input
          aria-label="Maximum distance from home (km)"
          type="number"
          min="0"
          step="1"
          disabled={homeLocation === null}
          value={filters.max_distance_km ?? ""}
          onChange={(event) =>
            updateFilters({
              max_distance_km:
                event.currentTarget.value === ""
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
      </label>
      {homeLocation === null && (
        <p className="filter-hint">
          Set a home location in Settings to use distance filtering.
        </p>
      )}

      <label>
        Search caches
        <input
          type="search"
          value={filters.text ?? ""}
          onChange={(event) =>
            updateFilters({ text: event.currentTarget.value || undefined })
          }
        />
      </label>
    </form>
  );
}
