import { expect, test } from "@playwright/test";

test("backend_health_is_visible", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Backend: ok");
});
