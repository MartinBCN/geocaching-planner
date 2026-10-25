import { HealthIndicator } from "../features/health/HealthIndicator";

interface PlaceholderPageProps {
  title: string;
  showHealth?: boolean;
}

// Placeholder pages until their features land; each shows its title.
export function PlaceholderPage({
  title,
  showHealth = false,
}: PlaceholderPageProps) {
  return (
    <section>
      <h1>{title}</h1>
      {showHealth ? <HealthIndicator /> : null}
    </section>
  );
}
