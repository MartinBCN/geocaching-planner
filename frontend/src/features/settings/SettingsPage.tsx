import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { MapView } from "../map/MapView";

type SettingsResponse = components["schemas"]["SettingsResponse"];
type SettingsPayload = components["schemas"]["SettingsPayload"];
type SettingsForm = {
  homeLatitude: string;
  homeLongitude: string;
  avgSpeedKmh: string;
  corridorMDefault: string;
  defaultProfile: SettingsPayload["default_profile"];
  tileUrl: string;
  tileAttribution: string;
};

const SETTINGS_KEY = ["settings"];

function toForm(settings: SettingsResponse): SettingsForm {
  return {
    homeLatitude: settings.home_location?.lat.toString() ?? "",
    homeLongitude: settings.home_location?.lon.toString() ?? "",
    avgSpeedKmh: settings.avg_speed_kmh.toString(),
    corridorMDefault: settings.corridor_m_default.toString(),
    defaultProfile: settings.default_profile,
    tileUrl: settings.tile_url,
    tileAttribution: settings.tile_attribution,
  };
}

async function fetchSettings(): Promise<SettingsResponse> {
  const { data, error } = await api.GET("/api/v1/settings");
  if (!data) {
    throw new Error(error?.title ?? "Unable to load settings.");
  }
  return data;
}

function validationMessages(form: SettingsForm): string[] {
  const errors: string[] = [];
  const speed = Number(form.avgSpeedKmh);
  const corridor = Number(form.corridorMDefault);
  const lat = Number(form.homeLatitude);
  const lon = Number(form.homeLongitude);

  if (!Number.isFinite(speed) || speed < 5 || speed > 50) {
    errors.push("Enter an average speed between 5 and 50 km/h.");
  }
  if (!Number.isInteger(corridor) || corridor < 50 || corridor > 5000) {
    errors.push("Enter a default corridor between 50 and 5000 meters.");
  }
  if (form.homeLatitude.trim() !== "" || form.homeLongitude.trim() !== "") {
    if (
      form.homeLatitude.trim() === "" ||
      form.homeLongitude.trim() === "" ||
      !Number.isFinite(lat) ||
      !Number.isFinite(lon) ||
      lat < -90 ||
      lat > 90 ||
      lon < -180 ||
      lon > 180
    ) {
      errors.push(
        "Enter both valid home coordinates (latitude −90 to 90, longitude −180 to 180).",
      );
    }
  }
  if (
    form.tileUrl.trim() !== "" &&
    !form.tileUrl.startsWith("http://") &&
    !form.tileUrl.startsWith("https://")
  ) {
    errors.push("Tile URL must use HTTP or HTTPS.");
  }
  if (form.tileAttribution.trim() === "") {
    errors.push("Tile attribution is required.");
  }
  return errors;
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: fetchSettings,
  });
  const [form, setForm] = useState<SettingsForm | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [showHomePicker, setShowHomePicker] = useState(false);

  useEffect(() => {
    if (settingsQuery.data) {
      setForm(toForm(settingsQuery.data));
    }
  }, [settingsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: async (payload: SettingsPayload) => {
      const { data, error } = await api.PUT("/api/v1/settings", {
        body: payload,
      });
      if (!data) {
        throw new Error(error?.title ?? "Unable to save settings.");
      }
      return data;
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(SETTINGS_KEY, settings);
      setForm(toForm(settings));
      setValidationErrors([]);
      setSaved(true);
    },
  });

  function updateField<K extends keyof SettingsForm>(
    field: K,
    value: SettingsForm[K],
  ) {
    setForm((current) => (current ? { ...current, [field]: value } : current));
    setValidationErrors([]);
    setSaved(false);
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) {
      return;
    }
    const errors = validationMessages(form);
    setValidationErrors(errors);
    setSaved(false);
    if (errors.length > 0) {
      return;
    }
    const homeLocation =
      form.homeLatitude.trim() === ""
        ? null
        : {
            lat: Number(form.homeLatitude),
            lon: Number(form.homeLongitude),
          };
    saveMutation.mutate({
      home_location: homeLocation,
      avg_speed_kmh: Number(form.avgSpeedKmh),
      corridor_m_default: Number(form.corridorMDefault),
      default_profile: form.defaultProfile,
      tile_url: form.tileUrl.trim() || null,
      tile_attribution: form.tileAttribution.trim(),
    });
  }

  if (settingsQuery.isPending) {
    return <p role="status">Loading settings…</p>;
  }
  if (settingsQuery.isError) {
    return <p role="alert">{settingsQuery.error.message}</p>;
  }
  if (!form) {
    return <p role="alert">Settings are unavailable.</p>;
  }

  return (
    <section className="settings-page">
      <h1>Settings</h1>
      <form className="settings-form" onSubmit={submit} noValidate>
        <fieldset>
          <legend>Home location</legend>
          <p>Leave both coordinates blank to clear your home location.</p>
          <button
            type="button"
            aria-expanded={showHomePicker}
            onClick={() => setShowHomePicker((current) => !current)}
          >
            {showHomePicker ? "Hide map picker" : "Pick home location on map"}
          </button>
          {showHomePicker && (
            <MapView
              className="home-location-map"
              homeLocation={
                form.homeLatitude.trim() !== "" &&
                form.homeLongitude.trim() !== "" &&
                Number.isFinite(Number(form.homeLatitude)) &&
                Number.isFinite(Number(form.homeLongitude))
                  ? {
                      lat: Number(form.homeLatitude),
                      lon: Number(form.homeLongitude),
                    }
                  : null
              }
              tileUrl={form.tileUrl}
              tileAttribution={form.tileAttribution}
              onLocationSelect={({ lat, lon }) => {
                updateField("homeLatitude", lat.toFixed(6));
                updateField("homeLongitude", lon.toFixed(6));
              }}
            />
          )}
          <div className="settings-coordinate-fields">
            <label>
              Home latitude
              <input
                inputMode="decimal"
                value={form.homeLatitude}
                onChange={(event) =>
                  updateField("homeLatitude", event.currentTarget.value)
                }
              />
            </label>
            <label>
              Home longitude
              <input
                inputMode="decimal"
                value={form.homeLongitude}
                onChange={(event) =>
                  updateField("homeLongitude", event.currentTarget.value)
                }
              />
            </label>
          </div>
        </fieldset>

        <label>
          Average cycling speed (km/h)
          <input
            type="number"
            min="5"
            max="50"
            step="1"
            value={form.avgSpeedKmh}
            onChange={(event) =>
              updateField("avgSpeedKmh", event.currentTarget.value)
            }
          />
        </label>

        <label>
          Default route corridor (meters)
          <input
            type="number"
            min="50"
            max="5000"
            step="1"
            value={form.corridorMDefault}
            onChange={(event) =>
              updateField("corridorMDefault", event.currentTarget.value)
            }
          />
        </label>

        <label>
          Default cycling profile
          <select
            value={form.defaultProfile}
            onChange={(event) =>
              updateField(
                "defaultProfile",
                event.currentTarget.value as SettingsForm["defaultProfile"],
              )
            }
          >
            <option value="trekking">Trekking</option>
            <option value="fastbike">Fast bike</option>
            <option value="safety">Safety</option>
          </select>
        </label>

        <label>
          Map tile URL
          <input
            value={form.tileUrl}
            onChange={(event) =>
              updateField("tileUrl", event.currentTarget.value)
            }
          />
        </label>

        <label>
          Map tile attribution
          <input
            value={form.tileAttribution}
            onChange={(event) =>
              updateField("tileAttribution", event.currentTarget.value)
            }
          />
        </label>

        {validationErrors.length > 0 && (
          <ul role="alert" className="settings-errors">
            {validationErrors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        )}
        {saveMutation.isError && (
          <p role="alert">{saveMutation.error.message}</p>
        )}
        {saved && <p role="status">Settings saved.</p>}

        <button type="submit" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving…" : "Save settings"}
        </button>
      </form>
    </section>
  );
}
