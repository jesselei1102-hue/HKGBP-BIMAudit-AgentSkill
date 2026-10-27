// GBP Model Audit window: one page, two views chosen by the tool result (choose_checks / show_overview).
import { App } from "@modelcontextprotocol/ext-apps";
import { renderChoose, type ChooseData } from "./choose";
import { renderOverview, type OverviewData } from "./overview";
import { applyInitialHostTheme, initTheme } from "./theme/theme";
import { createModelContext } from "./ui/context";
import { escapeHtml } from "./ui/html";

type ToolResult = { content?: { type: string; text?: string }[]; structuredContent?: unknown; isError?: boolean };

const view = document.getElementById("view")!;
const status = document.getElementById("status")!;
const subtitle = document.getElementById("subtitle")!;
let contextText = "GBP Model Audit window: waiting for data.";

const app = new App({ name: "GBP Model Audit", version: "0.1.0" });
const context = createModelContext(app, () => contextText);
initTheme(app, { toggle: document.getElementById("btn-theme") as HTMLButtonElement });

function setState(text: string) {
  contextText = text;
  context.schedule();
}

function dataFrom(result: ToolResult): Record<string, unknown> | undefined {
  if (result.structuredContent) return result.structuredContent as Record<string, unknown>;
  const text = result.content?.find((c) => c.type === "text")?.text;
  try {
    return text ? JSON.parse(text) : undefined;
  } catch {
    return undefined;
  }
}

function show(result: ToolResult) {
  const data = dataFrom(result);
  if (!data) return;
  if (data.view === "choose") {
    subtitle.textContent = "Choose checks";
    status.textContent = `Runs folder: ${String(data.runsRoot ?? "")}`;
    renderChoose(app, data as unknown as ChooseData, view, setState);
  } else if (data.view === "overview") {
    if (data.error) {
      subtitle.textContent = "Review";
      status.textContent = "";
      view.innerHTML = `<div class="empty"><b>Could not read this run</b><span>${escapeHtml(String(data.error))}</span></div>`;
      setState(`GBP Model Audit window: could not read the run - ${String(data.error)}`);
      return;
    }
    renderOverview(app, data as unknown as OverviewData, view, { status, subtitle }, setState);
  }
}

app.ontoolresult = (params) => show(params as ToolResult);

await app.connect();
applyInitialHostTheme(app);
