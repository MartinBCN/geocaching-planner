import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type HealthResponse = components["schemas"]["HealthResponse"];

export interface HealthReply {
  httpStatus: number;
  data: HealthResponse | undefined;
  problemTitle: string | undefined;
}

export const CHECKING_TEXT = "Checking backend…";
export const UNREACHABLE_TEXT =
  "Backend not reachable — is `mise run dev` running?";

function problemTitle(value: unknown): string | undefined {
  if (typeof value === "object" && value !== null && "title" in value) {
    const title: unknown = value.title;
    return typeof title === "string" && title.length > 0 ? title : undefined;
  }
  return undefined;
}

export async function fetchHealth(): Promise<HealthReply> {
  const { data, error, response } = await api.GET("/api/v1/health");
  return {
    httpStatus: response.status,
    data,
    problemTitle: problemTitle(error),
  };
}

// Maps a reply to the visible text (AC4). A 200 is "ok" only when the body says so; any
// other 2xx is degraded; a 5xx problem+json names its title.
export function describeHealth({
  httpStatus,
  data,
  problemTitle,
}: HealthReply): string {
  if (data !== undefined) {
    return httpStatus === 200 && data.status === "ok"
      ? "Backend: ok"
      : "Backend: degraded";
  }
  return problemTitle
    ? `Backend: degraded — ${problemTitle}`
    : "Backend: degraded";
}
