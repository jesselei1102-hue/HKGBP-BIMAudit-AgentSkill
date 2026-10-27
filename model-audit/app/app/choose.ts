// Window 1: choose which checks to run, then send the instruction to the chat.
import type { App } from "@modelcontextprotocol/ext-apps";
import { sendToChat } from "./chat";
import { joinPath, runPrompt } from "./logic/prompts";
import { groupState, groupsFor, toggleGroup, toggleTask } from "./logic/selection";
import { escapeHtml, pad3, plural } from "./ui/html";
import { initTabs } from "./ui/tabs";

type Task = { task: string; tl: string; name: string; summary: string; groups: string[] };
type Run = { name: string; groups: string[]; partial: boolean; hasReports: boolean; modified: string };
export type ChooseData = {
  view: "choose";
  catalogue: { groups: { id: string; name: string }[]; tasks: Task[] };
  runs: Run[];
  runsRoot: string;
  today: string;
  suggested: string;
};

export function renderChoose(app: App, data: ChooseData, view: HTMLElement, onState: (text: string) => void) {
  const cat = data.catalogue;
  let sel = new Set<string>();
  let search = "";
  let mode: "new" | "merge" = "new";
  let mergeRun = data.runs[0]?.name ?? "";
  let sent = false;

  const all = () => sel.size === cat.tasks.length;
  const existing = data.runs.map((r) => r.name);
  /** Same naming as newRunName in src/runs.ts: audit-<today>-full / -s10-s13 / -<n>tasks, -2 … when taken. */
  const runName = () => (mode === "merge" ? mergeRun : newName());
  const newName = () => {
    if (!sel.size) return data.suggested;
    const base = `audit-${data.today}${suffix()}`;
    let name = base;
    for (let i = 2; existing.includes(name); i++) name = `${base}-${i}`;
    return name;
  };
  const suffix = () => {
    if (all()) return "-full";
    const ids = cat.tasks.filter((t) => sel.has(t.task)).map((t) => t.task.replace(/^AUD-/, "").toLowerCase());
    return ids.length > 4 ? `-${ids.length}tasks` : ids.length ? `-${ids.join("-")}` : "";
  };

  view.innerHTML = `
    <section class="stats" aria-label="Summary">
      <div class="stat"><b>${pad3(cat.tasks.length)}</b><span>tasks</span></div>
      <div class="stat"><b data-k="sel">000</b><span>selected</span></div>
      <div class="stat"><b data-k="groups">000</b><span>groups</span></div>
    </section>
    <div class="toolbar">
      <label class="search">
        <svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
        <input data-k="search" type="search" placeholder="Search by number or name" autocomplete="off" />
      </label>
    </div>
    <nav class="tabs" role="tablist">
      ${cat.groups.map((g, i) => `<button class="tab" type="button" role="tab" data-tab="${escapeHtml(g.id)}"><span class="n">${String(i + 1).padStart(2, "0")}</span>${escapeHtml(g.name)} <span class="tab-count" data-count="${escapeHtml(g.id)}"></span></button>`).join("")}
    </nav>
    ${cat.groups.map((g) => `<section class="panel" id="panel-${escapeHtml(g.id)}" role="tabpanel" hidden>
      <div class="group-bar"><p class="meta">${escapeHtml(g.id)} · ${escapeHtml(g.name)}</p>
        <button class="text-link" type="button" data-group="${escapeHtml(g.id)}">Select group</button></div>
      <div class="table-wrap" data-table="${escapeHtml(g.id)}"></div></section>`).join("")}
    <section class="run-mode" aria-label="Where to put the results">
      <label><input type="radio" name="mode" value="new" checked /> New audit <span class="mono" data-k="folder"></span></label>
      <label><input type="radio" name="mode" value="merge" ${data.runs.length ? "" : "disabled"} /> Add to an existing audit
        ${data.runs.length
          ? `<select data-k="pick-run">${data.runs.map((r) => `<option value="${escapeHtml(r.name)}">${escapeHtml(r.name)}</option>`).join("")}</select>`
          : `<span class="mono">No earlier audits in ${escapeHtml(data.runsRoot)}</span>`}
      </label>
    </section>
    <p class="message" data-k="message" hidden></p>
    <footer class="dock">
      <div class="dock-group"><span class="count" data-k="count">0 selected</span></div>
      <div class="dock-group">
        <button class="db" type="button" data-k="clear">Clear</button>
        <button class="db pri" type="button" data-k="run" disabled>Run 0 checks</button>
      </div>
    </footer>`;

  const $ = <T extends HTMLElement = HTMLElement>(k: string) => view.querySelector<T>(`[data-k="${k}"]`)!;
  let tab = "";
  let ready = false;
  initTabs((name) => {
    tab = name;
    if (ready) onState(state());
  }, view);

  function rows(group: string) {
    const q = search.trim().toLowerCase();
    const list = cat.tasks.filter((t) => t.groups.includes(group) &&
      (!q || [t.task, t.tl, t.name, t.summary].some((v) => v.toLowerCase().includes(q))));
    if (!list.length) return `<div class="empty"><b>No tasks match</b><span>Try another number or name.</span></div>`;
    return `<table><thead><tr><th class="check-col"></th><th>TL</th><th>Task</th><th>Clause</th></tr></thead><tbody>${list
      .map((t) => {
        const others = t.groups.filter((g) => g !== group);
        return `<tr class="task-row${sel.has(t.task) ? " sel" : ""}" data-task="${escapeHtml(t.task)}">
          <td class="check-col"><input type="checkbox" ${sel.has(t.task) ? "checked" : ""} aria-label="Select ${escapeHtml(t.tl)}" /></td>
          <td class="tl">${escapeHtml(t.tl)}</td>
          <td>${escapeHtml(t.name)}${others.map((g) => `<span class="chip">Also in ${escapeHtml(g)}</span>`).join("")}</td>
          <td class="muted">${escapeHtml(t.summary)}</td></tr>`;
      })
      .join("")}</tbody></table>`;
  }

  function render() {
    for (const g of cat.groups) {
      view.querySelector(`[data-table="${g.id}"]`)!.innerHTML = rows(g.id);
      const n = cat.tasks.filter((t) => t.groups.includes(g.id) && sel.has(t.task)).length;
      view.querySelector(`[data-count="${g.id}"]`)!.textContent = n ? String(n) : "";
      view.querySelector(`[data-group="${g.id}"]`)!.textContent =
        groupState(sel, cat, g.id) === "all" ? "Clear group" : "Select group";
    }
    const groups = groupsFor(sel, cat);
    $("sel").textContent = pad3(sel.size);
    $("groups").textContent = pad3(groups.length);
    $("count").textContent = `${sel.size} selected`;
    $("folder").textContent = `Folder: ${newName()}`;
    const run = $<HTMLButtonElement>("run");
    run.textContent = sent ? "Sent" : `Run ${plural(sel.size, "check")}`;
    run.disabled = sent || sel.size === 0;
    onState(state());
  }

  function state() {
    const picked = cat.tasks.filter((t) => sel.has(t.task)).map((t) => t.tl);
    return [
      "GBP Model Audit window: choose checks.",
      `Selected (${picked.length}): ${picked.join(", ") || "none"}.`,
      `Results: ${mode === "merge" ? `add to existing audit ${mergeRun}` : `new audit ${runName()}`}.`,
      `Tab: ${tab}.`,
      sent ? "Instruction sent to the chat." : "",
    ].filter(Boolean).join("\n");
  }

  view.addEventListener("click", (e) => {
    const t = e.target as HTMLElement;
    const g = t.closest<HTMLElement>("[data-group]");
    if (g) {
      sel = toggleGroup(sel, cat, g.dataset.group!);
      return render();
    }
    const row = t.closest<HTMLElement>("tr[data-task]");
    if (row) {
      sel = toggleTask(sel, row.dataset.task!);
      return render();
    }
  });
  $<HTMLInputElement>("search").addEventListener("input", (e) => {
    search = (e.target as HTMLInputElement).value;
    render();
  });
  for (const r of view.querySelectorAll<HTMLInputElement>('input[name="mode"]'))
    r.addEventListener("change", () => {
      mode = r.value as "new" | "merge";
      render();
    });
  view.querySelector<HTMLSelectElement>('[data-k="pick-run"]')?.addEventListener("change", (e) => {
    mergeRun = (e.target as HTMLSelectElement).value;
    render();
  });
  $("clear").addEventListener("click", () => {
    sel = new Set();
    sent = false;
    render();
  });
  $("run").addEventListener("click", async () => {
    const tasks = cat.tasks.filter((t) => sel.has(t.task)).map((t) => t.task);
    const run = runName();
    const text = runPrompt({ tasks, groups: groupsFor(sel, cat), run, runDir: joinPath(data.runsRoot, run), mode,
                             all: all() });
    const ok = await sendToChat(app, text, view);
    const msg = $("message");
    msg.hidden = false;
    msg.textContent = ok
      ? "Sent to the chat. The agent will open the overview when the analysis is done."
      : "Paste the instruction into the chat to start.";
    sent = ok;
    render();
  });
  ready = true;
  render();
}
