import { NavLink, Outlet } from "react-router";

const NAV_ITEMS = [
  { to: "/", label: "Map" },
  { to: "/import", label: "Import" },
  { to: "/routes", label: "Routes" },
  { to: "/settings", label: "Settings" },
];

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Geocaching Planner</span>
        <nav aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
