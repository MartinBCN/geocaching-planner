import { Route, Routes } from "react-router";
import { AppShell } from "./AppShell";
import { NotFound } from "./NotFound";
import { PlaceholderPage } from "./PlaceholderPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<PlaceholderPage title="Map" showHealth />} />
        <Route path="import" element={<PlaceholderPage title="Import" />} />
        <Route path="routes" element={<PlaceholderPage title="Routes" />} />
        <Route path="routes/:id" element={<PlaceholderPage title="Route" />} />
        <Route path="caches/:gc" element={<PlaceholderPage title="Cache" />} />
        <Route path="settings" element={<PlaceholderPage title="Settings" />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
