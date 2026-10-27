import type { ExpressionSpecification } from "maplibre-gl";

export const markerColorExpression: ExpressionSpecification = [
  "case",
  ["==", ["get", "found"], true],
  "#15803d",
  [
    "match",
    ["get", "type"],
    "Traditional",
    "#2f855a",
    "Multi",
    "#d97706",
    "Mystery",
    "#7c3aed",
    "Letterbox",
    "#b45309",
    "EarthCache",
    "#0f766e",
    "Wherigo",
    "#2563eb",
    "Virtual",
    "#0891b2",
    "Event",
    "#db2777",
    "CITO",
    "#65a30d",
    "Mega",
    "#be123c",
    "Giga",
    "#9f1239",
    "Webcam",
    "#475569",
    "Lab",
    "#9333ea",
    "Other",
    "#64748b",
    "#64748b",
  ],
];

export const markerOpacityExpression: ExpressionSpecification = [
  "case",
  ["==", ["get", "available"], false],
  0.38,
  1,
];

export const markerStrokeWidthExpression: ExpressionSpecification = [
  "case",
  ["==", ["get", "corrected"], true],
  3,
  1,
];

export const markerStrokeColorExpression: ExpressionSpecification = [
  "case",
  ["==", ["get", "archived"], true],
  "#7f1d1d",
  ["==", ["get", "corrected"], true],
  "#111827",
  "#ffffff",
];
