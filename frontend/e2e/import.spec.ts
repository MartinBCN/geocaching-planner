import { expect, test } from "@playwright/test";

function syntheticCacheGpx(token: string): string {
  const caches = ["A", "B", "C"]
    .map(
      (suffix, index) =>
        `<wpt lat="52.${index + 1}" lon="4.${index + 1}"><name>GC${token}${suffix}</name>` +
        "<sym>Geocache</sym><extensions>" +
        `<gs:cache id="${index + 1}" available="True" archived="False">` +
        `<gs:name>Synthetic cache ${index + 1}</gs:name>` +
        "<gs:owner>Synthetic owner</gs:owner><gs:type>Traditional Cache</gs:type>" +
        "<gs:container>Small</gs:container><gs:difficulty>1.5</gs:difficulty>" +
        "<gs:terrain>2</gs:terrain>" +
        (index === 0
          ? "<gs:logs>" +
            `<gs:log id="${Date.now()}"><gs:date>2026-01-01T10:00:00Z</gs:date>` +
            "<gs:type>Found it</gs:type><gs:finder>Synthetic finder A</gs:finder>" +
            "<gs:text>First synthetic log</gs:text></gs:log>" +
            `<gs:log id="${Date.now() + 1}"><gs:date>2026-01-02T10:00:00Z</gs:date>` +
            "<gs:type>Write note</gs:type><gs:finder>Synthetic finder B</gs:finder>" +
            "<gs:text>Second synthetic log</gs:text></gs:log></gs:logs>"
          : "") +
        "</gs:cache></extensions></wpt>",
    )
    .join("");
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<gpx xmlns="http://www.topografix.com/GPX/1/0" ' +
    'xmlns:gs="http://www.groundspeak.com/cache/1/0" version="1.0">' +
    caches +
    "</gpx>"
  );
}

function syntheticWaypointGpx(token: string): string {
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<gpx xmlns="http://www.topografix.com/GPX/1/0" version="1.0">' +
    `<wpt lat="52.4" lon="4.4"><name>PK${token}A</name><cmt>Parking</cmt>` +
    "<desc>Parking area</desc><type>Waypoint|Parking Area</type></wpt>" +
    `<wpt lat="52.5" lon="4.5"><name>FN${token}B</name><cmt>Final</cmt>` +
    "<desc>Final location</desc><type>Waypoint|Final Location</type></wpt>" +
    "</gpx>"
  );
}

test("imports a synthetic Pocket Query and shows its summary", async ({
  page,
}) => {
  const token = Date.now().toString();
  await page.goto("/import");
  await page.getByLabel("Choose files…").setInputFiles([
    {
      name: "synthetic-pq.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(syntheticCacheGpx(token)),
    },
    {
      name: "synthetic-pq-wpts.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(syntheticWaypointGpx(token)),
    },
  ]);
  await page.getByRole("button", { name: "Import files" }).click();

  await expect(
    page.getByRole("heading", { name: "Import summary" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Import summary" })
      .getByText(/3 created, 0 updated, 0 unchanged, 2 waypoints/),
  ).toBeVisible();
  await expect(page.getByText(/synthetic-pq\.gpx/).first()).toBeVisible();
  await expect(page.getByText(/synthetic-pq-wpts\.gpx/).first()).toBeVisible();
});
