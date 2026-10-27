// Window 2/3: the results of one run, the reading review (the confirmation gate), and the reports once built.
import type { App } from "@modelcontextprotocol/ext-apps";
import type { Check, Mark, Overview, Reading, Status } from "../src/types";
import { sendToChat } from "./chat";
import { markPayload, preloadMarks } from "./logic/marks";
import { confirmPrompt, joinPath, rereadPrompt, unreviewedPrompt } from "./logic/prompts";
import { escapeHtml, pad3 } from "./ui/html";
import { initTabs } from "./ui/tabs";

export type OverviewData = { view: "overview"; overview: Overview; runsRoot: string; error?: string };
type ToolResult = { isError?: boolean; structuredContent?: unknown; content?: { type: string; text?: string }[] };

const ORDER: Status[] = ["FAIL", "UNCLEAR", "N/A", "PASS"];
const e = (v: unknown) => escapeHtml(v === null || v === undefined ? "" : String(v));
const errText = (r: ToolResult) => r.content?.find((c) => c.type === "text")?.text ?? "Unknown error";

function statusCell(s: Status) {
  const dot = s === "FAIL" ? '<i class="sig danger"></i>' : s === "UNCLEAR" ? '<i class="sig"></i>' : "";
  return `<span class="st">${dot}${s}</span>`;
}

export function renderOverview(
  app: App,
  data: OverviewData,
  view: HTMLElement,
  head: { status: HTMLElement; subtitle: HTMLElement },
  onState: (text: string) => void
) {
  const ov = data.overview;
  const runDir = joinPath(data.runsRoot, ov.run);
  // Window 3 only when the reports show these results; older reports (e.g. before a merge) leave the gate open.
  const hasReports = ov.reportsCurrent;
  const anyReports = !!(ov.reports.bim || ov.reports.ap);
  const marks = preloadMarks(ov.readings, ov.gate?.readings ?? []);
  const expanded = new Set(ov.tasks.filter((t) => t.counts.FAIL || t.counts.UNCLEAR).map((t) => t.task));
  let tab = "tasks";
  let ready = false;
  let busy = false;
  let sent = false;
  let lastAction = "";
  let cropsLoaded = false;

  head.subtitle.textContent = hasReports ? "Reports ready" : "Review";
  head.status.textContent = `Run ${ov.run}${ov.project ? ` · ${ov.project}` : ""}${ov.partial ? " · some tasks only" : ""}`;

  const counted = (m: Mark) => ov.readings.filter((r) => marks.get(r.id)?.mark === m).length;
  const unmarked = () => ov.readings.length - counted("ok") - counted("wrong");

  view.innerHTML = `
    <section class="stats" aria-label="Summary">
      <div class="stat"><b>${pad3(ov.counts.checks)}</b><span>checks</span></div>
      <div class="stat"><b>${pad3(ov.counts.fail)}</b><span>fail</span></div>
      <div class="stat"><b>${pad3(ov.counts.unclear)}</b><span><i class="sig"></i>to check yourself</span></div>
      <div class="stat"><b data-k="left">000</b><span>readings to review</span></div>
    </section>
    <nav class="tabs" role="tablist">
      <button class="tab" type="button" role="tab" data-tab="tasks"><span class="n">01</span>Tasks <span class="tab-count">${ov.tasks.length}</span></button>
      <button class="tab" type="button" role="tab" data-tab="readings"><span class="n">02</span>Readings <span class="tab-count" data-k="rcount"></span></button>
      <button class="tab" type="button" role="tab" data-tab="issues"><span class="n">03</span>Data issues <span class="tab-count">${ov.inputs.length + ov.warnings.length || ""}</span></button>
      ${anyReports ? `<button class="tab" type="button" role="tab" data-tab="reports"><span class="n">04</span>Reports${hasReports ? "" : " (earlier)"}</button>` : ""}
    </nav>
    <section class="panel" id="panel-tasks" role="tabpanel"><div class="table-wrap" data-k="tasks"></div></section>
    <section class="panel" id="panel-readings" role="tabpanel" hidden><div data-k="readings"></div></section>
    <section class="panel" id="panel-issues" role="tabpanel" hidden>${issues()}</section>
    ${anyReports ? `<section class="panel" id="panel-reports" role="tabpanel" hidden>${reports()}</section>` : ""}
    <p class="message" data-k="message" hidden></p>
    <footer class="dock" data-k="dock"></footer>`;

  const $ = <T extends HTMLElement = HTMLElement>(k: string) => view.querySelector<T>(`[data-k="${k}"]`)!;

  // ---------------------------------------------------------------- tasks
  function checkRows(list: Check[]) {
    return [...list]
      .sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status))
      .map((c) => `<tr><td>${statusCell(c.status)}</td><td>${e(c.item)}</td><td>${e(c.object)}</td><td>${e(c.expected)}</td>
        <td>${e(c.actual)}${c.status === "UNCLEAR" ? `<span class="yourself">${c.fix ? `Check this yourself: ${e(c.fix)}` : "Check this yourself."}</span>` : ""}</td>
        <td class="muted">${e(c.cite)}</td></tr>`)
      .join("");
  }

  function renderTasks() {
    if (!ov.tasks.length) {
      $("tasks").innerHTML = `<div class="empty"><b>No results in this run yet</b><span>The run folder has no analysis files. Run the analysis, then open the overview again.</span></div>`;
      return;
    }
    $("tasks").innerHTML = `<table><thead><tr><th>TL</th><th>Task</th><th>PASS</th><th>FAIL</th><th>UNCLEAR</th><th>N/A</th></tr></thead><tbody>${ov.tasks
      .map((t) => {
        const open = expanded.has(t.task);
        const row = `<tr class="task-row${open ? " sel" : ""}" data-task="${e(t.task)}"><td class="tl">${e(t.tl)}</td><td>${e(t.name)}</td>
          ${(["PASS", "FAIL", "UNCLEAR", "N/A"] as Status[]).map((s) => `<td class="num">${t.counts[s] || "·"}</td>`).join("")}</tr>`;
        if (!open) return row;
        const list = ov.checks.filter((c) => c.task === t.task);
        return row + `<tr class="detail-row"><td colspan="6"><table><thead><tr><th>Status</th><th>Item</th><th>Object</th><th>Expected</th><th>Actual</th><th>Clause</th></tr></thead><tbody>${checkRows(list)}</tbody></table></td></tr>`;
      })
      .join("")}</tbody></table>`;
  }

  // ---------------------------------------------------------------- readings
  function card(r: Reading) {
    const m = marks.get(r.id);
    return `<article class="reading${m?.mark === "ok" ? " marked-ok" : ""}" data-id="${e(r.id)}">
      <h3>${e(r.item || r.key)}</h3>
      <div class="crop" data-crop="${e(r.crop ?? "")}">${r.crop ? `<p class="meta">Loading crop…</p>` : `<p class="meta">No crop</p>`}</div>
      <dl class="detail">
        <dt>Value</dt><dd class="mono">${e(r.value) || "—"}</dd>
        <dt>Sheet</dt><dd>${e(r.sheet) || "—"}</dd>
        <dt>Finding</dt><dd>${e(r.finding) || "—"}</dd>
        <dt>Confidence</dt><dd>${e(r.confidence) || "—"}</dd>
        ${r.note ? `<dt>Note</dt><dd>${e(r.note)}</dd>` : ""}
        <dt>Key</dt><dd class="mono">${e(r.id)}</dd>
      </dl>
      <div class="seg" role="group" aria-label="Is this reading correct?">
        <button type="button" data-mark="ok" class="${m?.mark === "ok" ? "on" : ""}">Correct</button>
        <button type="button" data-mark="wrong" class="${m?.mark === "wrong" ? "on" : ""}">Wrong</button>
      </div>
      ${m?.mark === "wrong" ? `<input class="note" type="text" placeholder="What is wrong (optional)" value="${e(m.note)}" />` : ""}
    </article>`;
  }

  function renderReadings() {
    $("readings").innerHTML = ov.readings.length
      ? `<div class="cards-list">${ov.readings.map(card).join("")}</div>`
      : `<div class="empty"><b>No sheet readings in this run.</b><span>Nothing to review here.</span></div>`;
    cropsLoaded = false;
    if (tab === "readings") void loadCrops();
  }

  async function loadCrops() {
    if (cropsLoaded) return;
    cropsLoaded = true;
    for (const box of view.querySelectorAll<HTMLElement>(".crop[data-crop]")) {
      const file = box.dataset.crop;
      if (!file) continue;
      try {
        const r = (await app.callServerTool({ name: "get_crop", arguments: { run: ov.run, file } })) as ToolResult;
        const d = r.structuredContent as { mime?: string; base64?: string } | undefined;
        if (r.isError || !d?.base64) throw new Error(errText(r));
        box.innerHTML = `<img alt="Crop of the sheet" src="data:${e(d.mime)};base64,${d.base64}" />`;
      } catch {
        box.innerHTML = `<p class="meta">No crop</p>`;
      }
    }
  }

  // ---------------------------------------------------------------- issues and reports
  function issues() {
    if (!ov.inputs.length && !ov.warnings.length)
      return `<div class="empty"><b>No missing inputs or data warnings.</b><span>Every task had what it needed.</span></div>`;
    return `<div class="issues">
      ${ov.inputs.length ? `<h3>Missing inputs</h3>${ov.inputs.map((c) => `<div><p>${e(c.task)}: ${e(c.actual)}</p><p class="fix">How to fix: ${e(c.fix) || "see RUN.md"}</p></div>`).join("")}` : ""}
      ${ov.warnings.length ? `<h3>Data warnings</h3>${ov.warnings.map((w) => `<p>${e(w)}</p>`).join("")}` : ""}
    </div>`;
  }

  function reportPaths() {
    return [ov.reports.bim, ov.reports.ap, ...ov.reports.groups]
      .filter((p): p is string => !!p)
      .map((p) => joinPath(runDir, runDir.includes("\\") ? p.replaceAll("/", "\\") : p));
  }

  function reports() {
    const canOpen = !!app.getHostCapabilities()?.openLinks;
    const label = (p: string) =>
      p.endsWith("report-bim.html") ? "BIM team report" : p.endsWith("report-ap.html") ? "AP / client report" : "Group report";
    return `<table><thead><tr><th>Report</th><th>Path</th><th></th></tr></thead><tbody>${reportPaths()
      .map((p) => `<tr><td>${label(p)}</td><td class="report-path">${e(p)}</td><td>
        ${canOpen ? `<button class="text-link" type="button" data-open="${e(p)}">Open</button> ` : ""}
        <button class="text-link" type="button" data-copypath="${e(p)}">Copy path</button></td></tr>`)
      .join("")}</tbody></table>`;
  }

  // ---------------------------------------------------------------- dock and actions
  function renderDock() {
    const left = unmarked();
    const wrong = counted("wrong");
    $("left").textContent = pad3(left);
    $("rcount").textContent = ov.readings.length ? `${ov.readings.length - left}/${ov.readings.length}` : "";
    if (hasReports) {
      $("dock").innerHTML = `<div class="dock-group"><span class="count">Reports ready</span></div>
        <div class="dock-group"><button class="db pri" type="button" data-act="copy-reports">Copy report paths</button></div>`;
      return;
    }
    const pri =
      wrong > 0
        ? `<button class="db pri" type="button" data-act="reread" ${busy || sent ? "disabled" : ""}>Send back for re-reading</button>`
        : left === 0
          ? `<button class="db pri" type="button" data-act="confirm" ${busy || sent ? "disabled" : ""}>Confirm and build reports</button>`
          : `<button class="db pri" type="button" disabled>Mark every reading to confirm (${left} left)</button>`;
    $("dock").innerHTML = `<div class="dock-group"><span class="count">${left ? `${left} left to mark` : "All readings marked"}</span></div>
      <div class="dock-group">
        <span class="note-label">The reports will list the readings nobody checked.</span>
        <button class="db" type="button" data-act="unreviewed" ${busy || sent ? "disabled" : ""}>Build reports without full review</button>
        ${pri}
      </div>`;
  }

  function say(text: string, danger = false) {
    const m = $("message");
    m.hidden = false;
    m.innerHTML = `${danger ? '<i class="sig danger"></i>' : ""}${e(text)}`;
  }

  async function saveGate(mode: "confirmed" | "unreviewed"): Promise<boolean> {
    const payload = markPayload(marks, ov.readings);
    try {
      const r = (await app.callServerTool({ name: "save_gate", arguments: { run: ov.run, marks: payload, mode } })) as ToolResult;
      if (r.isError) throw new Error(errText(r));
      return true;
    } catch (err) {
      say(`Could not save the review: ${(err as Error).message}`, true);
      return false;
    }
  }

  async function act(kind: string) {
    if (busy) return;
    busy = true;
    renderDock();
    try {
      if (kind === "confirm") {
        if (await saveGate("confirmed")) await post(confirmPrompt(ov.run), "Review saved and sent to the chat. The agent builds the reports next.");
      } else if (kind === "unreviewed") {
        if (await saveGate("unreviewed"))
          await post(unreviewedPrompt(ov.run, unmarked()), "Review saved and sent to the chat. The reports will list the unchecked readings.");
      } else if (kind === "reread") {
        const wrong = ov.readings
          .filter((r) => marks.get(r.id)?.mark === "wrong")
          .map((r) => ({ id: r.id, sheet: r.sheet, item: r.item, note: marks.get(r.id)!.note }));
        await post(rereadPrompt(ov.run, wrong), "Sent back to the chat for re-reading.");
      } else if (kind === "copy-reports") {
        await copy(reportPaths().join("\n"));
        say("Report paths copied.");
      }
      lastAction = kind;
    } finally {
      busy = false;
      renderDock();
      state();
    }
  }

  async function post(text: string, okMessage: string) {
    const ok = await sendToChat(app, text, view);
    say(ok ? okMessage : "Paste the instruction into the chat to continue.");
    sent = ok;
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      say(text);
    }
  }

  function state() {
    if (!ready) return;
    onState(
      [
        `GBP Model Audit window: ${hasReports ? "reports ready" : "review"} for run ${ov.run}.`,
        `${ov.counts.checks} checks, ${ov.counts.fail} fail, ${ov.counts.unclear} to check yourself.`,
        `Readings: ${ov.readings.length} - ${counted("ok")} correct, ${counted("wrong")} wrong, ${unmarked()} not marked.`,
        `Tab: ${tab}.`,
        lastAction ? `Last action: ${lastAction}${sent ? " (sent to the chat)" : ""}.` : "",
      ].filter(Boolean).join("\n")
    );
  }

  view.addEventListener("click", async (ev) => {
    const t = ev.target as HTMLElement;
    const actBtn = t.closest<HTMLButtonElement>("[data-act]");
    if (actBtn && !actBtn.disabled) return act(actBtn.dataset.act!);
    const markBtn = t.closest<HTMLButtonElement>("[data-mark]");
    if (markBtn) {
      const cardEl = markBtn.closest<HTMLElement>(".reading")!;
      const id = cardEl.dataset.id!;
      const mark = markBtn.dataset.mark as Mark;
      if (marks.get(id)?.mark === mark) marks.delete(id);
      else marks.set(id, { mark, note: marks.get(id)?.note ?? "" });
      const r = ov.readings.find((x) => x.id === id)!;
      const img = cardEl.querySelector(".crop")!.innerHTML;
      cardEl.outerHTML = card(r);
      const fresh = view.querySelector<HTMLElement>(`.reading[data-id="${CSS.escape(id)}"]`)!;
      fresh.querySelector(".crop")!.innerHTML = img;
      fresh.querySelector<HTMLInputElement>("input.note")?.focus();
      renderDock();
      return state();
    }
    const row = t.closest<HTMLElement>("tr.task-row[data-task]");
    if (row) {
      const id = row.dataset.task!;
      if (expanded.has(id)) expanded.delete(id);
      else expanded.add(id);
      renderTasks();
      return state();
    }
    const open = t.closest<HTMLElement>("[data-open]");
    if (open) {
      const r = await app.openLink({ url: "file:///" + open.dataset.open!.replaceAll("\\", "/") }).catch(() => ({ isError: true }));
      if ((r as { isError?: boolean }).isError) say("This chat cannot open local files. Copy the path instead.");
      return;
    }
    const cp = t.closest<HTMLElement>("[data-copypath]");
    if (cp) {
      await copy(cp.dataset.copypath!);
      say("Path copied.");
    }
  });
  view.addEventListener("input", (ev) => {
    const input = ev.target as HTMLInputElement;
    if (!input.classList.contains("note")) return;
    const id = input.closest<HTMLElement>(".reading")!.dataset.id!;
    const m = marks.get(id);
    if (m) m.note = input.value;
    state();
  });

  initTabs((name) => {
    tab = name;
    if (name === "readings") void loadCrops();
    state();
  }, view);
  renderTasks();
  renderReadings();
  renderDock();
  ready = true;
  state();
}
