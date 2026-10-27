import { describe, expect, it } from "vitest";
import {
  markerColorExpression,
  markerOpacityExpression,
  markerStrokeColorExpression,
  markerStrokeWidthExpression,
} from "./styles";

describe("cache marker styles", () => {
  it("uses a distinct found-cache color and cache-type palette", () => {
    expect(markerColorExpression).toContainEqual([
      "==",
      ["get", "found"],
      true,
    ]);
    const colorExpression = JSON.stringify(markerColorExpression);
    expect(colorExpression).toContain("Traditional");
    expect(colorExpression).toContain("Mystery");
  });

  it("dims disabled caches and highlights corrected locations", () => {
    expect(markerOpacityExpression).toContainEqual([
      "==",
      ["get", "available"],
      false,
    ]);
    expect(markerStrokeWidthExpression).toContainEqual([
      "==",
      ["get", "corrected"],
      true,
    ]);
    expect(markerStrokeColorExpression).toContainEqual([
      "==",
      ["get", "corrected"],
      true,
    ]);
  });
});
