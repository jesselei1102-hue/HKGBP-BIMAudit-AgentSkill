// Window 1: choose which checks to run (steps bar, sections on the left, tasks on the right), then say what happens next.
import type { App } from "@modelcontextprotocol/ext-apps";
import { sendToChat } from "./chat";
import { singleFlight } from "./logic/once";
import { joinPath, runPrompt } from "./logic/prompts";
import { groupsFor, sectionState, toggleSection, toggleTask } from "./logic/selection";
import { escapeHtml, plural } from "./ui/html";
import { navHtml, stepsHtml } from "./ui/steps";

type Task = { task: string; tl: string; name: string; summary: string; groups: string[]; section: string };
type Run = { name: string; groups: string[]; partial: boolean; hasReports: boolean; modified: string };
export type ChooseData = {
  view: "choose";
  catalogue: { sections: { id: string; name: string; clause: string }[]; groups: { id: string; name: string }[]; tasks: Task[] };
  runs: Run[];
  runsRoot: string;
  today: string;
  suggested: string;
};

/** One line under each section name: what kind of tasks it holds. */
const SECTION_NOTE: Record<string, string> = {
  views: "drawings on the sheets",
  schedules: "tables on the sheets",
  assembly: "sheets, colours and export",
  health: "the model itself",
};

export function renderChoose(app: App, data: ChooseData, view: HTMLElement, onState: (text: string) => void) {
  const cat = data.catalogue;
  let sel = new Set<string>();
  let section = cat.sections[0]?.id ?? "";
  let search = "";
  let mode: "new" | "merge" = "new";
  let mergeRun = data.runs[0]?.name ?? "";

  const all = () => sel.size === cat.tasks.length;
  const existing = data.runs.map((r) => r.name);
  const inSection = (id: string) => cat.tasks.filter((t) => t.section === id);
  const picked = () => cat.tasks.filter((t) => sel.has(t.task));
  /** Same naming as newRunName in src/runs.ts: audit-<today>-full / -s10-s13 / -<n>tasks, -2 … when taken. */
  const newName = () => {
    if (!sel.size) return data.suggested;
    const ids = picked().map((t) => t.task.replace(/^AUD-/, "").toLowerCase());
    const base = `audit-${data.today}-${all() ? "full" : ids.length > 4 ? `${ids.length}tasks` : ids.join("-")}`;
    let name = base;
    for (let i = 2; existing.includes(name); i++) name = `${base}-${i}`;
    return name;
  };
  const runName = () => (mode === "merge" ? mergeRun : newName());

  view.innerHTML = `
    ${stepsHtml(1)}
    <div class="layout">
      <div data-k="side"></div>
      <section class="pane">
        <div class="pane-head"><h2 data-k="title"></h2><button class="text-link" type="button" data-k="sec-toggle"></button></div>
        <p class="pane-why" data-k="why"></p>
        <label class="search">
          <svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input data-k="search" type="search" placeholder="Search by number or name" autocomplete="off" />
        </label>
        <div data-k="list"></div>
        <div class="save-line" data-k="save"></div>
      </section>
    </div>
    <footer class="dock">
      <div class="dock-group"><span class="count" data-k="count"></span></div>
      <div class="dock-group"><button class="db pri" type="button" data-k="run" disabled>Run 0 checks</button></div>
    </footer>`;

  const $ = <T extends HTMLElement = HTMLElement>(k: string) => view.querySelector<T>(`[data-k="${k}"]`)!;

  function renderSide() {
    const items = cat.sections.map((s) => {
      const total = inSection(s.id).length;
      const n = inSection(s.id).filter((t) => sel.has(t.task)).length;
      return { id: s.id, label: s.name, count: `${n}/${total}`, tone: n ? ("unclear" as const) : ("muted" as const) };
    });
    const extra = `<div class="side-extra">
      <button type="button" class="side-item" data-quick="all">Full audit (all ${cat.tasks.length})</button>
      <button type="button" class="side-item" data-quick="clear">Clear</button></div>`;
    $("side").innerHTML = navHtml(items, section).replace("</nav>", `${extra}</nav>`);
  }

  function renderPane() {
    const s = cat.sections.find((x) => x.id === section)!;
    const total = inSection(section).length;
    $("title").textContent = s.name;
    $("why").textContent = `${s.clause} · ${SECTION_NOTE[section] ?? ""}`;
    $("sec-toggle").textContent = sectionState(sel, cat, section) === "all" ? "Clear section" : `Select all ${total}`;
    const q = search.trim().toLowerCase();
    const list = inSection(section).filter((t) => !q || [t.task, t.tl, t.name, t.summary].some((v) => v.toLowerCase().includes(q)));
    $("list").innerHTML = list.length
      ? list.map((t) => `<label class="task-line${sel.has(t.task) ? " sel" : ""}" data-task="${escapeHtml(t.task)}">
          <input type="checkbox" ${sel.has(t.task) ? "checked" : ""} />
          <span><span>${escapeHtml(t.name)}</span><br /><span class="sub">${escapeHtml(t.tl)} · ${escapeHtml(t.summary.replace(/^BIMGBPS\s*/, ""))}</span></span>
        </label>`).join("")
      : `<div class="empty"><b>No tasks match</b><span>Try another number or name.</span></div>`;
  }

  function renderSave() {
    if (mode === "new") {
      $("save").innerHTML = `Results go to a new audit <b class="mono">${escapeHtml(newName())}</b> · ` + (data.runs.length
        ? `<button class="text-link" type="button" data-k="merge-on">Add to an earlier audit instead</button>`
        : `<span>No earlier audits in ${escapeHtml(data.runsRoot)}</span>`);
    } else {
      $("save").innerHTML = `Results are added to <select data-k="pick-run">${data.runs.map((r) =>
        `<option value="${escapeHtml(r.name)}"${r.name === mergeRun ? " selected" : ""}>${escapeHtml(r.name)}</option>`).join("")}</select> · ` +
        `<button class="text-link" type="button" data-k="merge-off">Back to a new audit</button>`;
    }
  }

  function renderDock() {
    const names = cat.sections.filter((s) => inSection(s.id).some((t) => sel.has(t.task))).map((s) => s.name);
    $("count").textContent = sel.size ? `${plural(sel.size, "check")} selected · ${names.join(", ")}` : "Nothing selected";
    const run = $<HTMLButtonElement>("run");
    run.textContent = `Run ${plural(sel.size, "check")}`;
    run.disabled = sel.size === 0;
  }

  function render(pane = true) {
    renderSide();
    if (pane) renderPane();
    renderSave();
    renderDock();
    onState(state());
  }

  function state() {
    return [
      "GBP Model Audit window: choose checks.",
      `Selected (${sel.size}): ${picked().map((t) => t.tl).join(", ") || "none"}.`,
      `Results: ${mode === "merge" ? `add to existing audit ${mergeRun}` : `new audit ${runName()}`}.`,
      `Section shown: ${section}.`,
    ].join("\n");
  }

  /** After Run: the window explains the next steps instead of staying on the list. */
  function renderNext(text: string, sent: boolean, box: Element | null) {
    const names = picked().map((t) => t.name);
    view.innerHTML = `
      ${stepsHtml(2)}
      <section class="pane">
        <div class="pane-head"><h2>${sent ? "Sent to the agent" : "Ready to send"}</h2></div>
        <p class="pane-why">${escapeHtml(plural(names.length, "check"))}: ${escapeHtml(names.slice(0, 6).join(", "))}${names.length > 6 ? ` +${names.length - 6} more` : ""}</p>
        <div class="next-step now"><b>2 · The agent reads the model and runs the checks</b>
          <p>${sent ? "Read-only, through the Revit MCP. Follow its progress in the chat. Keep Revit open and idle (no dialogs)."
                    : "Paste the instruction below into the chat to start."}</p></div>
        <div class="next-step"><b>3 · A review window opens in the chat</b>
          <p>You look at the failures, the items to check yourself and the sheet readings, then confirm.</p></div>
        <div class="next-step"><b>4 · Reports</b><p>BIM team and AP / client editions, in the audit folder.</p></div>
        ${sent ? `<p class="pane-why">Instruction sent: "${escapeHtml(text.slice(0, 70))}…" <button class="text-link" type="button" data-k="show-sent">Show</button></p>
                  <pre class="mono pane-why" data-k="sent-text" hidden>${escapeHtml(text)}</pre>` : ""}
      </section>
      <footer class="dock"><div class="dock-group"><span class="count">${sent ? "Waiting for the agent" : "Waiting for you to paste the instruction"}</span></div>
        <div class="dock-group"><button class="db pri" type="button" disabled>${sent ? "Sent" : "Not sent"}</button></div></footer>`;
    if (box) view.querySelector(".dock")!.before(box);
    view.querySelector('[data-k="show-sent"]')?.addEventListener("click", () => {
      const pre = view.querySelector<HTMLElement>('[data-k="sent-text"]')!;
      pre.hidden = !pre.hidden;
    });
    onState(`GBP Model Audit window: ${sent ? "instruction sent to the chat" : "instruction shown for copying"} (${plural(names.length, "check")}, run ${runName()}).`);
  }

  const run = singleFlight(async () => {
    const name = runName();
    const text = runPrompt({ tasks: picked().map((x) => x.task), groups: groupsFor(sel, cat), run: name,
                             runDir: joinPath(data.runsRoot, name), mode, all: all() });
    $<HTMLButtonElement>("run").disabled = true;
    const ok = await sendToChat(app, text, view);
    renderNext(text, ok, ok ? null : view.querySelector(".prompt-box"));
  });

  view.addEventListener("click", async (e) => {
    const t = e.target as HTMLElement;
    const nav = t.closest<HTMLElement>("[data-nav]");
    if (nav) {
      section = nav.dataset.nav!;
      search = "";
      $<HTMLInputElement>("search").value = "";
      return render();
    }
    const quick = t.closest<HTMLElement>("[data-quick]");
    if (quick) {
      sel = quick.dataset.quick === "all" ? new Set(cat.tasks.map((x) => x.task)) : new Set();
      return render();
    }
    if (t.closest('[data-k="sec-toggle"]')) {
      sel = toggleSection(sel, cat, section);
      return render();
    }
    const line = t.closest<HTMLElement>("[data-task]");
    if (line && t.tagName === "INPUT") {
      sel = toggleTask(sel, line.dataset.task!);
      return render();
    }
    if (t.closest('[data-k="merge-on"]')) {
      mode = "merge";
      return render(false);
    }
    if (t.closest('[data-k="merge-off"]')) {
      mode = "new";
      return render(false);
    }
    if (t.closest('[data-k="run"]') && sel.size) return run();
  });
  view.addEventListener("change", (e) => {
    const t = e.target as HTMLElement;
    if (t.matches('[data-k="pick-run"]')) {
      mergeRun = (t as HTMLSelectElement).value;
      render(false);
    }
  });
  view.addEventListener("input", (e) => {
    const t = e.target as HTMLInputElement;
    if (t.matches('[data-k="search"]')) {
      search = t.value;
      renderPane();
    }
  });
  render();
}
