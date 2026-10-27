// The shared frame of both windows: the steps bar (Choose › Analyse › Review › Reports) and the side list.
import { escapeHtml } from "./html";

const STEPS = ["Choose", "Analyse", "Review", "Reports"];

export function stepsHtml(current: 1 | 2 | 3 | 4): string {
  return `<ol class="steps" aria-label="Audit steps">${STEPS.map((name, i) => {
    const n = i + 1;
    const cls = n < current ? ' class="done"' : n === current ? ' class="now" aria-current="step"' : "";
    return `<li${cls}>${n} ${name}</li>`;
  }).join("")}</ol>`;
}

export type NavItem = { id: string; label: string; count?: string; tone?: "fail" | "unclear" | "muted"; done?: boolean };

/** Side list (a row of tabs on narrow windows, by CSS). Buttons carry data-nav; the selected one has class "sel". */
export function navHtml(items: NavItem[], selected: string): string {
  return `<nav class="side" aria-label="Lists">${items.map((it) => {
    const count = it.count ? `<span class="count ${it.tone ?? "muted"}">${escapeHtml(it.count)}</span>` : "";
    const tick = it.done ? `<span class="tick" aria-label="done">✓</span>` : "";
    return `<button type="button" data-nav="${escapeHtml(it.id)}" class="side-item${it.id === selected ? " sel" : ""}">` +
      `${count}<span class="side-label">${escapeHtml(it.label)}</span>${tick}</button>`;
  }).join("")}</nav>`;
}

/** The tick button at the top of a review list; secondary, since the dock holds the one primary button. */
export function seenButtonHtml(key: string, label: string, seen: boolean): string {
  return `<button class="db" type="button" data-seen="${escapeHtml(key)}">${seen ? "Seen ✓" : escapeHtml(label)}</button>`;
}
