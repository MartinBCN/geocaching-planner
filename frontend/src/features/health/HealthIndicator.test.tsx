import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { createQueryClient } from "../../api/queryClient";
import { server } from "../../test/server";
import { HealthIndicator } from "./HealthIndicator";

function renderIndicator() {
  const client = createQueryClient(false);
  return render(
    <QueryClientProvider client={client}>
      <HealthIndicator />
    </QueryClientProvider>,
  );
}

describe("HealthIndicator", () => {
  it("shows the checking text while health is pending", () => {
    server.use(http.get("*/api/v1/health", () => new Promise<never>(() => {})));
    renderIndicator();

    expect(screen.getByRole("status").textContent).toBe("Checking backend…");
  });

  it("shows Backend: ok for a 200 with status ok", async () => {
    server.use(
      http.get("*/api/v1/health", () =>
        HttpResponse.json({ status: "ok", version: "0.1.0", db: "ok" }),
      ),
    );
    renderIndicator();

    expect(await screen.findByText("Backend: ok")).toBeTruthy();
  });

  it("shows Backend: degraded for a 200 with another status", async () => {
    server.use(
      http.get("*/api/v1/health", () =>
        HttpResponse.json({
          status: "degraded",
          version: "0.1.0",
          db: "error",
        }),
      ),
    );
    renderIndicator();

    expect(await screen.findByText("Backend: degraded")).toBeTruthy();
  });

  it("shows the problem title for a 5xx problem+json response", async () => {
    server.use(
      http.get("*/api/v1/health", () =>
        HttpResponse.json(
          {
            type: "about:blank",
            title: "Database unavailable",
            status: 500,
            detail: "connection refused",
            instance: "/api/v1/health",
          },
          {
            status: 500,
            headers: { "Content-Type": "application/problem+json" },
          },
        ),
      ),
    );
    renderIndicator();

    expect(
      await screen.findByText("Backend: degraded — Database unavailable"),
    ).toBeTruthy();
  });

  it("shows the unreachable message when the request fails", async () => {
    server.use(http.get("*/api/v1/health", () => HttpResponse.error()));
    renderIndicator();

    expect(
      await screen.findByText(
        "Backend not reachable — is `mise run dev` running?",
      ),
    ).toBeTruthy();
  });
});
