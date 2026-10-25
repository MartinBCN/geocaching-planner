import { expectTypeOf } from "vitest";
import { api } from "./client";
import type { components } from "./schema";

type HealthResponse = components["schemas"]["HealthResponse"];

// AC2: the health call carries the exact generated HealthResponse type (no any).
export async function healthIsTyped(): Promise<void> {
  const { data } = await api.GET("/api/v1/health");
  expectTypeOf(data).toEqualTypeOf<HealthResponse | undefined>();
  expectTypeOf<HealthResponse["status"]>().toEqualTypeOf<"ok" | "degraded">();
}

// AC2: a path that is not in the generated schema is rejected at compile time.
export async function unknownPathIsRejected(): Promise<void> {
  // @ts-expect-error /api/v1/unknown is not an API path
  await api.GET("/api/v1/unknown");
}
