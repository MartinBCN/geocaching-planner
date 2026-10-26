import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";

export const server = setupServer(
  http.get("*/api/v1/health", () =>
    HttpResponse.json({ status: "ok", version: "test", db: "ok" }),
  ),
  http.get("*/api/v1/settings", () =>
    HttpResponse.json({
      home_location: null,
      avg_speed_kmh: 18,
      corridor_m_default: 500,
      default_profile: "trekking",
      tile_url:
        "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
      tile_attribution: "© OpenStreetMap contributors, CyclOSM",
    }),
  ),
);
