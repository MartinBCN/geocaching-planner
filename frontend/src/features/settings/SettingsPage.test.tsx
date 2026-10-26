import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { createQueryClient } from "../../api/queryClient";
import { server } from "../../test/server";
import { SettingsPage } from "./SettingsPage";

const defaultSettings = {
  home_location: null,
  avg_speed_kmh: 18,
  corridor_m_default: 500,
  default_profile: "trekking",
  tile_url: "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
  tile_attribution: "© OpenStreetMap contributors, CyclOSM",
};

function renderSettings() {
  return render(
    <QueryClientProvider client={createQueryClient(false)}>
      <SettingsPage />
    </QueryClientProvider>,
  );
}

describe("SettingsPage", () => {
  it("loads, edits, and saves settings", async () => {
    server.use(
      http.get("*/api/v1/settings", () => HttpResponse.json(defaultSettings)),
      http.put(
        "*/api/v1/settings",
        async ({ request }) =>
          new Response(await request.text(), {
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    renderSettings();

    const speed = await screen.findByLabelText("Average cycling speed (km/h)");
    fireEvent.change(speed, { target: { value: "24" } });
    fireEvent.change(screen.getByLabelText("Home latitude"), {
      target: { value: "52.1" },
    });
    fireEvent.change(screen.getByLabelText("Home longitude"), {
      target: { value: "4.3" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));

    expect(await screen.findByText("Settings saved.")).toBeTruthy();
    expect(
      screen.getByLabelText("Average cycling speed (km/h)"),
    ).toHaveProperty("value", "24");
  });

  it("shows validation errors without submitting invalid settings", async () => {
    let submitted = false;
    server.use(
      http.get("*/api/v1/settings", () => HttpResponse.json(defaultSettings)),
      http.put("*/api/v1/settings", () => {
        submitted = true;
        return HttpResponse.json(defaultSettings);
      }),
    );
    renderSettings();

    const speed = await screen.findByLabelText("Average cycling speed (km/h)");
    fireEvent.change(speed, { target: { value: "4" } });
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));

    expect(
      await screen.findByText("Enter an average speed between 5 and 50 km/h."),
    ).toBeTruthy();
    await waitFor(() => expect(submitted).toBe(false));
  });
});
