import { useQuery } from "@tanstack/react-query";
import {
  CHECKING_TEXT,
  describeHealth,
  fetchHealth,
  UNREACHABLE_TEXT,
} from "./health";

const REFRESH_INTERVAL_MS = 15_000;

// Polls every 15 s and refetches on window focus, so a stopped backend is not shown as "ok".
export function HealthIndicator() {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: REFRESH_INTERVAL_MS,
  });

  let text = CHECKING_TEXT;
  if (query.isError) {
    text = UNREACHABLE_TEXT;
  } else if (query.data !== undefined) {
    text = describeHealth(query.data);
  }

  return (
    <p role="status" className="health-indicator">
      {text}
    </p>
  );
}
