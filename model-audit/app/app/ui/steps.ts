// The side list of the window: BIMGBPS sections with how many of their checks are chosen.
import { escapeHtml } from "./html";

export type NavItem = { id: string; label: string; count?: string; tone?: "unclear" | "muted" };

/** Side list (a row of tabs on narrow windows, by CSS). Buttons carry data-nav; the selected one has class "sel". */
export function navHtml(items: NavItem[], selected: string): string {
  return `<nav class="side" aria-label="Sections">${items.map((it) => {
    const count = it.count ? `<span class="count ${it.tone ?? "muted"}">${escapeHtml(it.count)}</span>` : "";
    return `<button type="button" data-nav="${escapeHtml(it.id)}" class="side-item${it.id === selected ? " sel" : ""}"` +
      `${it.id === selected ? ' aria-current="true"' : ""}>${count}<span class="side-label">${escapeHtml(it.label)}</span></button>`;
  }).join("")}</nav>`;
}
