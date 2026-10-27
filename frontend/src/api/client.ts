import createClient from "openapi-fetch";
import type { paths } from "./schema";

// The schema paths already include the /api/v1 prefix, so the base is the bare origin.
// fetch is resolved per call so interceptors installed after import (MSW in tests) apply.
export const api = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (request) => globalThis.fetch(request),
});

type ImportPath = paths["/api/v1/imports"];
type ImportOperation = NonNullable<ImportPath["post"]>;
type ImportUploadPaths = Omit<paths, "/api/v1/imports"> & {
  "/api/v1/imports": Omit<ImportPath, "post"> & {
    post: Omit<ImportOperation, "requestBody"> & {
      requestBody: {
        content: {
          "multipart/form-data": { files: File[] };
        };
      };
    };
  };
};

export const importApi = createClient<ImportUploadPaths>({
  baseUrl: window.location.origin,
  fetch: (request) => globalThis.fetch(request),
});
