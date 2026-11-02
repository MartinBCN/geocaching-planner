import { expect, test } from "@playwright/test";

test("shares filters with map and list, restores the URL, and highlights a hovered cache", async ({
  page,
}) => {
  const listRequests: URLSearchParams[] = [];
  const markerRequests: URLSearchParams[] = [];
  const settings = {
    home_location: { lat: 52.1, lon: 4.1 },
    avg_speed_kmh: 18,
    corridor_m_default: 500,
    default_profile: "trekking",
    tile_url: "https://tiles.example/{z}/{x}/{y}.png",
    tile_attribution: "Synthetic attribution",
  };
  const cache = {
    gc_code: "GC1ABC",
    name: "Synthetic filter cache",
    type: "Traditional",
    container: "Small",
    difficulty: 1.5,
    terrain: 2,
    distance_km: 1.2,
    found_by_me: false,
    is_available: true,
    is_archived: false,
    has_corrected: false,
    lat: 52.1,
    lon: 4.1,
    placed_at: null,
  };

  await page.route("**/api/v1/settings", (route) =>
    route.fulfill({ json: settings }),
  );
  await page.route("**/api/v1/caches?*", (route) => {
    listRequests.push(new URL(route.request().url()).searchParams);
    return route.fulfill({ json: { items: [cache], total: 51 } });
  });
  await page.route("**/api/v1/caches/markers?*", (route) => {
    markerRequests.push(new URL(route.request().url()).searchParams);
    return route.fulfill({
      json: {
        items: [
          [
            "GC1ABC",
            "Synthetic filter cache",
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
        ],
        truncated: false,
        total: 1,
      },
    });
  });
  await page.route("https://tiles.example/**", (route) =>
    route.fulfill({ status: 204 }),
  );

  await page.goto("/?types=Traditional&found=false");
  await expect(page.getByRole("row", { name: /GC1ABC/ })).toBeVisible();
  await expect(
    page.getByRole("checkbox", { name: "Traditional" }),
  ).toBeChecked();
  await expect
    .poll(() =>
      listRequests.some(
        (params) =>
          params.getAll("types").includes("Traditional") &&
          params.get("found") === "false",
      ),
    )
    .toBe(true);

  const mysteryFilter = page.getByRole("checkbox", { name: "Mystery" });
  await expect(mysteryFilter).not.toBeChecked();
  await mysteryFilter.click();
  await expect(mysteryFilter).toBeChecked();
  await expect
    .poll(() =>
      listRequests.some(
        (params) =>
          params.getAll("types").includes("Mystery") &&
          params.getAll("types").includes("Traditional"),
      ),
    )
    .toBe(true);
  await expect
    .poll(() =>
      markerRequests.some(
        (params) =>
          params.getAll("types").includes("Mystery") &&
          params.getAll("types").includes("Traditional"),
      ),
    )
    .toBe(true);
  await expect(page).toHaveURL(/types=Traditional.*types=Mystery/);

  await page.reload();
  await expect(page.getByRole("checkbox", { name: "Mystery" })).toBeChecked();
  await expect(page.getByRole("row", { name: /GC1ABC/ })).toBeVisible();
  await page.getByRole("row", { name: /GC1ABC/ }).hover();
  await expect(page.getByTestId("cache-map")).toHaveAttribute(
    "data-highlighted-cache",
    "GC1ABC",
  );
});
