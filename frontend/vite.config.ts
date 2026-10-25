/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig(({ mode }) => {
  // The shared .env lives at the repository root, not in frontend/.
  const env = loadEnv(mode, repoRoot, "VITE_");
  const apiTarget = env.VITE_API_TARGET ?? "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      // ADR-0002: loopback only. Never bind to 0.0.0.0.
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": { target: apiTarget, changeOrigin: false },
      },
    },
    test: {
      environment: "jsdom",
      environmentOptions: {
        jsdom: { url: "http://localhost:5173/" },
      },
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      coverage: {
        provider: "v8",
        include: ["src/**"],
        // ADR-0008: only the generated API schema is excluded from coverage.
        exclude: [
          "src/api/schema.d.ts",
          "src/**/*.test.{ts,tsx}",
          "src/**/*.test-d.ts",
          "src/test/**",
        ],
        thresholds: { lines: 80 },
      },
    },
  };
});
