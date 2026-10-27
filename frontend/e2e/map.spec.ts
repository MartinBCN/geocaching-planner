import { expect, test } from "@playwright/test";

test("shows imported cache markers at their locations with popup and attribution", async ({
  page,
}) => {
  const settingsResponse = await page.request.get("/api/v1/settings");
  expect(settingsResponse.ok()).toBeTruthy();
  const originalSettings: unknown = await settingsResponse.json();
  const settings = originalSettings as {
    home_location: { lat: number; lon: number } | null;
    avg_speed_kmh: number;
    corridor_m_default: number;
    default_profile: "trekking" | "fastbike" | "safety";
    tile_url: string;
    tile_attribution: string;
  };
  const homeLocation = { lat: 52.1, lon: 4.1 };
  const updateSettings = await page.request.put("/api/v1/settings", {
    data: { ...settings, home_location: homeLocation },
  });
  expect(updateSettings.ok()).toBeTruthy();

  const token = Date.now().toString();
  const gcCode = `GC${token}A`;
  const gpx =
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<gpx xmlns="http://www.topografix.com/GPX/1/0" ' +
    'xmlns:gs="http://www.groundspeak.com/cache/1/0" version="1.0">' +
    `<wpt lat="${homeLocation.lat}" lon="${homeLocation.lon}">` +
    `<name>${gcCode}</name><sym>Geocache</sym><extensions>` +
    '<gs:cache id="1" available="True" archived="False">' +
    `<gs:name>Synthetic map cache ${token}</gs:name>` +
    "<gs:owner>Synthetic owner</gs:owner><gs:type>Traditional Cache</gs:type>" +
    "<gs:container>Small</gs:container><gs:difficulty>1.5</gs:difficulty>" +
    "<gs:terrain>2</gs:terrain></gs:cache></extensions></wpt></gpx>";

  try {
    await page.goto("/import");
    await page.getByLabel("Choose files…").setInputFiles({
      name: "synthetic-map-cache.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(gpx),
    });
    await page.getByRole("button", { name: "Import files" }).click();
    await expect(
      page.getByRole("heading", { name: "Import summary" }),
    ).toBeVisible();

    await page.goto("/");
    const map = page.getByTestId("cache-map");
    await expect(map).toBeVisible();
    await expect(map).toHaveAttribute("data-marker-source-ready", "true");
    await expect(
      page.getByText("© OpenStreetMap contributors, CyclOSM"),
    ).toBeVisible();
    const mapBounds = await map.boundingBox();
    if (!mapBounds) {
      throw new Error("The cache map has no visible bounding box.");
    }
    await map.click({
      position: {
        x: mapBounds.width / 2,
        y: mapBounds.height / 2,
      },
    });
    await expect(page.getByText(`Synthetic map cache ${token}`)).toBeVisible();
    await expect(page.getByText(gcCode)).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Cache details" }),
    ).toHaveAttribute("href", `/caches/${gcCode}`);
  } finally {
    const restoreSettings = await page.request.put("/api/v1/settings", {
      data: settings,
    });
    expect(restoreSettings.ok()).toBeTruthy();
  }
});
