// Window 2/3: results overview, the confirmation gate, and the reports once built. (Filled in by the next step.)
import type { App } from "@modelcontextprotocol/ext-apps";

export type OverviewData = { view: "overview"; overview: unknown; runsRoot: string; error?: string };

export function renderOverview(
  _app: App,
  _data: OverviewData,
  view: HTMLElement,
  _head: { status: HTMLElement; subtitle: HTMLElement },
  _onState: (text: string) => void
) {
  view.innerHTML = `<div class="empty"><b>Overview</b><span>Not built yet.</span></div>`;
}
