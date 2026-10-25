import { QueryClient } from "@tanstack/react-query";

export function createQueryClient(retry: number | boolean = 1): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry } },
  });
}
