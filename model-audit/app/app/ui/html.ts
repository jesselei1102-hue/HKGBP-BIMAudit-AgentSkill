/** Escape text before inserting it into HTML strings. */
export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/** Monospace stat style: zero-pad below 1000 ("007"), "—" when unknown. */
export function pad3(value: number | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value < 1000 ? String(value).padStart(3, "0") : String(value);
}

/** Wrap 12×12 line-glyph markup (categories are told apart by shape, not colour). */
export function glyph(svgInner: string): string {
  return `<svg class="glyph" viewBox="0 0 12 12" aria-hidden="true">${svgInner}</svg>`;
}

export function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}
