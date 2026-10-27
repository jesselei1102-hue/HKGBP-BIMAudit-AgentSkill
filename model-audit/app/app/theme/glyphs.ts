import { glyph } from "../ui/html";

/**
 * Abstract 12×12 line glyphs for Revit categories — categories are told apart by shape, not colour.
 * Stroke only (svg.glyph sets fill none, stroke currentColor, width 1.4). Keep every shape distinct.
 * The Revit Schedule app keeps a copy of this table in mcp-app/src/mcp-app.ts — sync by hand.
 */
export const CATEGORY_GLYPHS: Record<string, string> = {
  // Architecture
  Walls: '<rect x="1" y="4" width="10" height="4"/>',
  Doors: '<path d="M2.5 11V1.5h7V11"/>',
  Windows: '<rect x="1.5" y="1.5" width="9" height="9"/><path d="M6 1.5v9M1.5 6h9"/>',
  Floors: '<path d="M1 7.5l5-3 5 3-5 3z"/>',
  Ceilings: '<path d="M1 3.5h10M3 3.5v3M9 3.5v3"/>',
  Roofs: '<path d="M1 9.5l5-6 5 6"/>',
  Stairs: '<path d="M1 10.5h3v-3h3v-3h3v-3"/>',
  Railings: '<path d="M1 3h10M2 3v8M6 3v8M10 3v8"/>',
  Ramps: '<path d="M1 10h10L1 4.5z"/>',
  Rooms: '<rect x="1.5" y="1.5" width="9" height="9" stroke-dasharray="2 1.6"/>',
  Furniture: '<path d="M2 5.5h8v3H2zM3 8.5v2.5M9 8.5v2.5"/>',
  Casework: '<rect x="1.5" y="2" width="9" height="8"/><path d="M6 2v8"/>',
  "Generic Models": '<path d="M6 1l5 3v4l-5 3-5-3V4z"/>',
  Mass: '<path d="M6 1l4.5 2.5v5L6 11 1.5 8.5v-5zM6 6v5M6 6l4.5-2.5M6 6L1.5 3.5"/>',
  "Curtain Panels": '<rect x="2.5" y="1" width="7" height="10"/><path d="M4.5 5.5l2.5-2.5M4.5 8.5l4-4"/>',
  "Curtain Wall Mullions": '<path d="M3 1.5h6M3 10.5h6M6 1.5v9"/>',
  "Specialty Equipment": '<circle cx="6" cy="6" r="2"/><circle cx="6" cy="6" r="4.5" stroke-dasharray="1.6 1.3"/>',

  // Structure
  Columns: '<rect x="4" y="1" width="4" height="10"/>',
  "Structural Columns": '<rect x="4" y="1" width="4" height="10"/><path d="M4 6h4"/>',
  "Structural Framing": '<path d="M1 4h10M1 8h10M3 4v4M9 4v4"/>',
  "Structural Foundations": '<path d="M1 9h10M2.5 9V6h7v3"/>',

  // Plumbing — round sections and bends
  Pipes: '<circle cx="6" cy="6" r="4.5"/><circle cx="6" cy="6" r="1.8"/>',
  "Pipe Fittings": '<path d="M2 1.5V7a3.5 3.5 0 0 0 3.5 3.5h5"/>',
  "Pipe Accessories": '<path d="M1 3.5v5l10-5v5z"/>',
  "Plumbing Fixtures": '<path d="M1.5 5h9A4.5 4.5 0 0 1 1.5 5zM6 5V1.5"/>',

  // HVAC — rectangular sections and square bends
  Ducts: '<rect x="1.5" y="3" width="9" height="6"/><path d="M1.5 3l9 6M10.5 3l-9 6"/>',
  "Duct Fittings": '<path d="M1.5 1.5h4v5h5v4h-9z"/>',
  "Duct Accessories": '<rect x="1.5" y="3" width="9" height="6"/><path d="M4 9l4-6"/>',
  "Mechanical Equipment": '<rect x="1.5" y="1.5" width="9" height="9"/><circle cx="6" cy="6" r="2.5"/>',

  // Electrical — dashed runs, panels, outlets, lights
  "Lighting Fixtures": '<circle cx="6" cy="6" r="2.5"/><path d="M6 1v1.5M6 9.5V11M1 6h1.5M9.5 6H11"/>',
  "Electrical Fixtures": '<circle cx="6" cy="6" r="4.5"/><path d="M4.5 4.5v3M7.5 4.5v3"/>',
  "Electrical Equipment": '<rect x="2" y="1.5" width="8" height="9"/><path d="M6.5 3L4.5 6.5h3L5.5 9"/>',
  Conduits: '<path d="M1 4.5h10M1 7.5h10" stroke-dasharray="2 1.5"/>',
  "Conduit Fittings": '<path d="M2 1.5V7a3.5 3.5 0 0 0 3.5 3.5h5" stroke-dasharray="2 1.5"/>',
  "Cable Trays": '<path d="M1 4v4h10V4"/>',
  "Cable Tray Fittings": '<path d="M1.5 1.5v9h9M4.5 1.5v6h6"/>',

  // Site
  Planting: '<circle cx="6" cy="4.5" r="3.5"/><path d="M6 8v3.5"/>',
  Site: '<path d="M1 8.5c2.5-3 4.5 0 7-2.5 1-1 2-1 3-.5M1 4.5c2-2 3.5 0 5.5-1.5"/>',
  Topography: '<path d="M1 8.5c2.5-3 4.5 0 7-2.5 1-1 2-1 3-.5M1 4.5c2-2 3.5 0 5.5-1.5"/>',
  Parking: '<rect x="1.5" y="1.5" width="9" height="9"/><path d="M4.5 9V3.5h2a1.6 1.6 0 0 1 0 3.2h-2"/>',
};

export const DEFAULT_GLYPH = '<circle cx="6" cy="6" r="4"/>';

/** The glyph svg for a category name (trimmed); unknown categories get a plain circle. */
export function categoryGlyph(category: string): string {
  return glyph(CATEGORY_GLYPHS[category.trim()] ?? DEFAULT_GLYPH);
}
