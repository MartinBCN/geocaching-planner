import { useState } from "react";
import { NavLink, Outlet } from "react-router";
import { ImportActivityContext } from "./ImportActivityContext";

const NAV_ITEMS = [
  { to: "/", label: "Map" },
  { to: "/import", label: "Import" },
  { to: "/routes", label: "Routes" },
  { to: "/settings", label: "Settings" },
];

export function AppShell() {
  const [isImporting, setIsImporting] = useState(false);

  function confirmNavigation(event: React.MouseEvent<HTMLElement>) {
    if (!isImporting) {
      return;
    }
    if (!(event.target instanceof Element)) {
      return;
    }
    const link = event.target.closest("a");
    if (link && link.pathname !== window.location.pathname) {
      if (!window.confirm("An import is in progress. Leave this page?")) {
        event.preventDefault();
      }
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Geocaching Planner</span>
        <nav aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={confirmNavigation}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <ImportActivityContext.Provider value={{ isImporting, setIsImporting }}>
        <main className="app-main">
          <Outlet />
        </main>
      </ImportActivityContext.Provider>
    </div>
  );
}
