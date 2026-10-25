import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";

export const server = setupServer(
  http.get("*/api/v1/health", () =>
    HttpResponse.json({ status: "ok", version: "test", db: "ok" }),
  ),
);
