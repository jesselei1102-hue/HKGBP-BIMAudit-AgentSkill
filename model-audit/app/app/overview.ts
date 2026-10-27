// Window 2/3: the results of one run as a to-do list (failures, items to check yourself, missing inputs, sheet readings),
// the confirmation gate, and the reports once built.
import type { App } from "@modelcontextprotocol/ext-apps";
import type { Check, Mark, Overview, Reading, Status } from "../src/types";
import { copyText, sendToChat } from "./chat";
import { groupChecks, type CheckGroup } from "./logic/groups";
import { markPayload, preloadMarks } from "./logic/marks";
import { confirmPrompt, joinPath, openReportPrompt, rereadPrompt, unreviewedPrompt } from "./logic/prompts";
import { reviewState, type Seen } from "./logic/review";
import { escapeHtml } from "./ui/html";
import { navHtml, stepsHtml, type NavItem } from "./ui/steps";

export type OverviewData = {
  view: "overview";
  overview: Overview;
  sections?: { id: string; name: string; clause: string }[];
  runsRoot: string;
  error?: string;
};
type ToolResult = { isError?: boolean; structuredContent?: unknown; content?: { type: string; text?: string }[] };
type ListKey = keyof Seen;

const ORDER: Status[] = ["FAIL", "UNCLEAR", "N/A", "PASS"];
const SHOWN_OBJECTS = 4;
const e = (v: unknown) => escapeHtml(v === null || v === undefined ? "" : String(v));
const errText = (r: ToolResult) => r.content?.find((c) => c.type === "text")?.text ?? "Unknown error";
const isInput = (c: Check) => c.id.endsWith("-INPUT");

/** Heading, one line on what the list is, and the button that ticks it off. */
const LISTS: Record<ListKey | "readings", { title: string; why: string; button?: string }> = {
  failures: { title: "Failures", why: "Problems in the model. Nothing to do here except note them; fix in Revit later.", button: "I've seen these" },
  check_yourself: { title: "Check yourself", why: "The tool could not decide. Each line says what to look at.", button: "I've checked these" },
  inputs: { title: "Missing inputs", why: "Optional data not taken this run. Each line says how to add it.", button: "I've seen these" },
  readings: { title: "Sheet readings", why: "Values read off the sheets. Compare each with its crop." },
};

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
  // Step 4 only when the reports show these results; older reports (e.g. before a merge) leave the gate open.
  const hasReports = ov.reportsCurrent;
  const anyReports = !!(ov.reports.bim || ov.reports.ap);
  const marks = preloadMarks(ov.readings, ov.gate?.readings ?? []);
  const seen: Seen = { failures: false, check_yourself: false, inputs: false, ...ov.gate?.reviewed };
  const taskOrder = ov.tasks.map((t) => t.task);
  const tlOf = new Map(ov.tasks.map((t) => [t.task, t.tl]));
  const nameOf = new Map(ov.tasks.map((t) => [t.task, t.name]));
  const failures = groupChecks(ov.checks.filter((c) => c.status === "FAIL" && !isInput(c)), taskOrder);
  const yourself = groupChecks(ov.checks.filter((c) => c.status === "UNCLEAR" && !isInput(c)), taskOrder);
  const nFail = failures.reduce((n, g) => n + g.checks.length, 0);
  const nYourself = yourself.reduce((n, g) => n + g.checks.length, 0);
  const nInputs = ov.inputs.length + ov.warnings.length;
  const openGroups = new Set<string>();
  const allObjects = new Set<string>();
  const expanded = new Set(ov.tasks.filter((t) => t.counts.FAIL || t.counts.UNCLEAR).map((t) => t.task));
  const crops = new Map<string, string>();
  let showMarked = false;
  let ready = false;
  let busy = false;
  let sent = false;
  let lastAction = "";

  head.subtitle.textContent = hasReports ? "Reports ready" : "Review";
  head.status.textContent = `Run ${ov.run}${ov.project ? ` · ${ov.project}` : ""}${ov.partial ? " · some tasks only" : ""}`;

  const counted = (m: Mark) => ov.readings.filter((r) => marks.get(r.id)?.mark === m).length;
  const unmarked = () => ov.readings.length - counted("ok") - counted("wrong");
  const review = () => reviewState({ failures: nFail, checkYourself: nYourself, inputs: nInputs,
                                     readingsLeft: unmarked(), readingsWrong: counted("wrong"), seen, reportsReady: hasReports });

  let list: string = anyReports && hasReports ? "reports" : "failures";
  if (!hasReports) {
    const done = review().done;
    list = (["failures", "check_yourself", "inputs", "readings"] as const).find((k) => !done[k]) ?? "failures";
  }

  view.innerHTML = `
    ${stepsHtml(hasReports ? 4 : 3)}
    <div class="layout">
      <div data-k="side"></div>
      <section class="pane" data-k="pane"></section>
    </div>
    <p class="message" data-k="message" hidden></p>
    <footer class="dock" data-k="dock"></footer>`;

  const $ = <T extends HTMLElement = HTMLElement>(k: string) => view.querySelector<T>(`[data-k="${k}"]`)!;

  // ---------------------------------------------------------------- side list
  function renderSide() {
    const done = review().done;
    const n = (v: number) => (v ? String(v) : "None");
    const items: NavItem[] = [
      ...(anyReports ? [{ id: "reports", label: hasReports ? "Reports" : "Reports (earlier)" }] : []),
      { id: "failures", label: LISTS.failures.title, count: n(nFail), tone: nFail ? "fail" : "muted", done: done.failures },
      { id: "check_yourself", label: LISTS.check_yourself.title, count: n(nYourself), tone: nYourself ? "unclear" : "muted", done: done.check_yourself },
      { id: "inputs", label: LISTS.inputs.title, count: n(nInputs), tone: "muted", done: done.inputs },
      { id: "readings", label: LISTS.readings.title, count: ov.readings.length ? String(unmarked()) : "None",
        tone: unmarked() ? "unclear" : "muted", done: done.readings },
      { id: "all", label: `All checks (${ov.counts.checks})` },
    ];
    $("side").innerHTML = navHtml(items, list);
  }

  // ---------------------------------------------------------------- pane
  function paneHead(key: ListKey | "readings") {
    const l = LISTS[key];
    const btn = key !== "readings" && l.button && !hasReports
      ? `<button class="db${seen[key as ListKey] ? "" : " pri"}" type="button" data-seen="${key}">${seen[key as ListKey] ? "Seen ✓" : l.button}</button>`
      : "";
    return `<div class="pane-head"><h2>${l.title}</h2>${btn}</div><p class="pane-why">${l.why}</p>`;
  }

  function groupCard(g: CheckGroup) {
    const tone = g.status === "FAIL" ? "fail" : "unclear";
    const all = allObjects.has(g.key);
    const objs = (all ? g.objects : g.objects.slice(0, SHOWN_OBJECTS))
      .map((o) => `${e(o.object)}${o.actual ? ` · ${e(o.actual)}` : ""}`).join("; ");
    const more = !all && g.objects.length > SHOWN_OBJECTS
      ? ` <button class="text-link" type="button" data-more="${e(g.key)}">+${g.objects.length - SHOWN_OBJECTS} more</button>` : "";
    const fixes = g.status === "FAIL"
      ? g.fixes.map((f) => `<p class="fix">Fix: ${e(f)}</p>`).join("")
      : (g.fixes.length ? g.fixes : ["the drawings for this item."]).map((f) => `<p class="fix">Look at${f === "the drawings for this item." ? "" : ":"} ${e(f)}</p>`).join("");
    const open = openGroups.has(g.key);
    return `<article class="group">
      <div class="group-head" data-group="${e(g.key)}" role="button" tabindex="0" aria-expanded="${open}">
        <span class="count ${tone}">${g.checks.length}</span><span class="tl">${e(tlOf.get(g.task) ?? g.task)}</span><span class="gi">${e(g.item)}</span>
      </div>
      <p class="objs">${objs}${more}</p>
      ${fixes}
      ${open ? `<div class="group-detail table-wrap"><table><thead><tr><th>Object</th><th>Expected</th><th>Actual</th><th>Clause</th></tr></thead><tbody>${g.checks
        .map((c) => `<tr><td>${e(c.object)}</td><td>${e(c.expected)}</td><td>${e(c.actual)}</td><td class="muted">${e(c.cite)}</td></tr>`).join("")}</tbody></table></div>` : ""}
    </article>`;
  }

  function groupsPane(key: "failures" | "check_yourself", groups: CheckGroup[]) {
    return paneHead(key) + (groups.length
      ? groups.map(groupCard).join("")
      : `<div class="empty"><b>None</b><span>${key === "failures" ? "No check failed." : "Every check could be decided."}</span></div>`);
  }

  function inputsPane() {
    if (!nInputs) return paneHead("inputs") + `<div class="empty"><b>None</b><span>Every task had what it needed.</span></div>`;
    return paneHead("inputs") + `<div class="issues">
      ${ov.inputs.map((c) => `<div class="group"><div class="group-head"><span class="tl">${e(tlOf.get(c.task) ?? c.task)}</span><span class="gi">${e(nameOf.get(c.task) ?? c.task)}</span></div>
        <p class="objs">${e(c.actual)}</p><p class="fix">How to fix: ${e(c.fix) || "see RUN.md"}</p></div>`).join("")}
      ${ov.warnings.length ? `<h3>Data warnings</h3>${ov.warnings.map((w) => `<p>${e(w)}</p>`).join("")}` : ""}
    </div>`;
  }

  function card(r: Reading) {
    const m = marks.get(r.id);
    return `<article class="reading${m?.mark === "ok" ? " marked-ok" : ""}" data-id="${e(r.id)}">
      <h3>${e(r.item || r.key)}</h3>
      <div class="crop" data-crop="${e(r.crop ?? "")}">${r.crop ? crops.get(r.crop) ?? `<p class="meta">Loading crop…</p>` : `<p class="meta">No crop</p>`}</div>
      <dl class="detail">
        <dt>Value</dt><dd class="mono">${e(r.value) || "—"}</dd>
        <dt>Sheet</dt><dd>${e(r.sheet) || "—"}</dd>
        <dt>Finding</dt><dd>${e(r.finding) || "—"}</dd>
        <dt>Confidence</dt><dd>${e(r.confidence) || "—"}</dd>
        ${r.note ? `<dt>Note</dt><dd>${e(r.note)}</dd>` : ""}
        <dt>Key</dt><dd class="mono">${e(r.id)}</dd>
      </dl>
      ${hasReports ? "" : `<div class="seg" role="group" aria-label="Is this reading correct?">
        <button type="button" data-mark="ok" class="${m?.mark === "ok" ? "on" : ""}">Correct</button>
        <button type="button" data-mark="wrong" class="${m?.mark === "wrong" ? "on" : ""}">Wrong</button>
      </div>`}
      ${m?.mark === "wrong" ? `<input class="note" type="text" placeholder="What is wrong (optional)" value="${e(m.note)}" />` : ""}
    </article>`;
  }

  /** Readings marked Correct fold away; unmarked and Wrong ones stay open (Wrong needs a note and goes back). */
  function readingsPane() {
    if (!ov.readings.length) return paneHead("readings") + `<div class="empty"><b>None</b><span>No sheet readings in this run.</span></div>`;
    const open = ov.readings.filter((r) => marks.get(r.id)?.mark !== "ok");
    const done = ov.readings.filter((r) => marks.get(r.id)?.mark === "ok");
    return paneHead("readings") +
      (open.length ? `<div class="cards-list">${open.map(card).join("")}</div>` : `<div class="empty"><b>Every reading is marked Correct</b><span></span></div>`) +
      (done.length ? `<p><button class="text-link" type="button" data-k="toggle-marked">${showMarked ? "Hide" : "Show"} the ${done.length} marked ${showMarked ? "▾" : "▸"}</button></p>
        ${showMarked ? `<div class="cards-list">${done.map(card).join("")}</div>` : ""}` : "");
  }

  function checkRows(rows: Check[]) {
    return [...rows]
      .sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status))
      .map((c) => `<tr><td>${statusCell(c.status)}</td><td>${e(c.item)}</td><td>${e(c.object)}</td><td>${e(c.expected)}</td>
        <td>${e(c.actual)}${c.status === "UNCLEAR" ? `<span class="yourself">${c.fix ? `Check this yourself: ${e(c.fix)}` : "Check this yourself."}</span>` : ""}</td>
        <td class="muted">${e(c.cite)}</td></tr>`)
      .join("");
  }

  function allPane() {
    const headHtml = `<div class="pane-head"><h2>All checks</h2></div><p class="pane-why">Every task in this run, by BIMGBPS section. Click a task for its checks.</p>`;
    if (!ov.tasks.length)
      return headHtml + `<div class="empty"><b>No results in this run yet</b><span>The run folder has no analysis files. Run the analysis, then open the overview again.</span></div>`;
    const sectionOf = new Map((data.sections ?? []).map((x) => [x.id, x]));
    let shown = "";
    return headHtml + `<div class="table-wrap"><table><thead><tr><th>TL</th><th>Task</th><th>PASS</th><th>FAIL</th><th>UNCLEAR</th><th>N/A</th></tr></thead><tbody>${ov.tasks
      .map((t) => {
        const sec = sectionOf.get(t.section);
        const heading = sec && t.section !== shown
          ? `<tr class="section-row"><td colspan="6">${e(sec.name)} · ${e(sec.clause)}</td></tr>` : "";
        shown = t.section;
        const open = expanded.has(t.task);
        const row = `<tr class="task-row${open ? " sel" : ""}" data-task="${e(t.task)}"><td class="tl">${e(t.tl)}</td><td>${e(t.name)}</td>
          ${(["PASS", "FAIL", "UNCLEAR", "N/A"] as Status[]).map((s) => `<td class="num">${t.counts[s] || "·"}</td>`).join("")}</tr>`;
        if (!open) return heading + row;
        const rows = ov.checks.filter((c) => c.task === t.task);
        return heading + row + `<tr class="detail-row"><td colspan="6"><table><thead><tr><th>Status</th><th>Item</th><th>Object</th><th>Expected</th><th>Actual</th><th>Clause</th></tr></thead><tbody>${checkRows(rows)}</tbody></table></td></tr>`;
      })
      .join("")}</tbody></table></div>`;
  }

  function reportPaths() {
    return [ov.reports.bim, ov.reports.ap, ...ov.reports.groups]
      .filter((p): p is string => !!p)
      .map((p) => joinPath(runDir, runDir.includes("\\") ? p.replaceAll("/", "\\") : p));
  }

  function reportsPane() {
    const label = (p: string) =>
      p.endsWith("report-bim.html") ? "BIM team report" : p.endsWith("report-ap.html") ? "AP / client report" : "Group report";
    return `<div class="pane-head"><h2>Reports</h2></div>
      <p class="pane-why">${hasReports ? "Built from these results. Open asks the agent to open the report in your browser."
                                       : "Built before the latest results. Review and build again to update them."}</p>
      <div class="table-wrap"><table><thead><tr><th>Report</th><th>Path</th><th></th></tr></thead><tbody>${reportPaths()
      .map((p) => `<tr><td>${label(p)}</td><td class="report-path">${e(p)}</td><td>
        <button class="text-link" type="button" data-open="${e(p)}" title="Asks the agent to open it">Open</button>
        <button class="text-link" type="button" data-copypath="${e(p)}">Copy path</button></td></tr>`)
      .join("")}</tbody></table></div>`;
  }

  function renderPane() {
    const html =
      list === "failures" ? groupsPane("failures", failures)
      : list === "check_yourself" ? groupsPane("check_yourself", yourself)
      : list === "inputs" ? inputsPane()
      : list === "readings" ? readingsPane()
      : list === "reports" ? reportsPane()
      : allPane();
    $("pane").innerHTML = html;
    if (list === "readings") void loadCrops();
  }

  async function loadCrops() {
    for (const box of view.querySelectorAll<HTMLElement>(".crop[data-crop]")) {
      const file = box.dataset.crop;
      if (!file) continue;
      if (crops.has(file)) {
        box.innerHTML = crops.get(file)!;
        continue;
      }
      let html = `<p class="meta">No crop</p>`;
      try {
        const r = (await app.callServerTool({ name: "get_crop", arguments: { run: ov.run, file } })) as ToolResult;
        const d = r.structuredContent as { mime?: string; base64?: string } | undefined;
        if (r.isError || !d?.base64) throw new Error(errText(r));
        html = `<img alt="Crop of the sheet" src="data:${e(d.mime)};base64,${d.base64}" />`;
      } catch {
        // keeps "No crop"
      }
      crops.set(file, html);
      // the pane may have been redrawn while the crop loaded
      for (const b of view.querySelectorAll<HTMLElement>(`.crop[data-crop="${CSS.escape(file)}"]`)) b.innerHTML = html;
    }
  }

  // ---------------------------------------------------------------- dock and actions
  function renderDock() {
    const s = review();
    const off = busy || sent ? "disabled" : "";
    const without = `<button class="db" type="button" data-act="unreviewed" title="The reports will list what nobody checked." ${off}>Build without full review</button>`;
    const pri =
      s.dock === "reports" ? `<button class="db pri" type="button" data-act="copy-reports">Copy report paths</button>`
      : s.dock === "wrong" ? `${without}<button class="db pri" type="button" data-act="reread" ${off}>Send back for re-reading</button>`
      : s.dock === "ready" ? `<button class="db pri" type="button" data-act="confirm" ${off}>Build reports</button>`
      : `${without}<button class="db pri" type="button" disabled>Build reports</button>`;
    $("dock").innerHTML = `<div class="dock-group"><span class="count">${e(s.label)}</span></div><div class="dock-group">${pri}</div>`;
  }

  function render() {
    renderSide();
    renderPane();
    renderDock();
    state();
  }

  function say(text: string, danger = false) {
    const m = $("message");
    m.hidden = false;
    m.innerHTML = `${danger ? '<i class="sig danger"></i>' : ""}${e(text)}`;
  }

  async function saveGate(mode: "confirmed" | "unreviewed"): Promise<boolean> {
    const payload = markPayload(marks, ov.readings);
    const { done } = review();
    const reviewed = { failures: done.failures, check_yourself: done.check_yourself, inputs: done.inputs };
    try {
      const r = (await app.callServerTool({ name: "save_gate", arguments: { run: ov.run, marks: payload, mode, reviewed } })) as ToolResult;
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
          await post(unreviewedPrompt(ov.run, unmarked()), "Review saved and sent to the chat. The reports will list what nobody checked.");
      } else if (kind === "reread") {
        const wrong = ov.readings
          .filter((r) => marks.get(r.id)?.mark === "wrong")
          .map((r) => ({ id: r.id, sheet: r.sheet, item: r.item, note: marks.get(r.id)!.note }));
        await post(rereadPrompt(ov.run, wrong), "Sent back to the chat for re-reading.");
      } else if (kind === "copy-reports") {
        const ok = await copyText(reportPaths().join("\n"), view);
        say(ok ? "Report paths copied." : "Press Ctrl+C to copy the selected paths.");
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

  function state() {
    if (!ready) return;
    const s = review();
    onState(
      [
        `GBP Model Audit window: ${hasReports ? "reports ready" : "review"} for run ${ov.run}.`,
        `${ov.counts.checks} checks, ${nFail} fail, ${nYourself} to check yourself, ${nInputs} missing inputs or warnings.`,
        `Readings: ${ov.readings.length} - ${counted("ok")} correct, ${counted("wrong")} wrong, ${unmarked()} not marked.`,
        `Review: ${s.label} (failures ${s.done.failures ? "seen" : "not seen"}, check yourself ${s.done.check_yourself ? "checked" : "not checked"}, inputs ${s.done.inputs ? "seen" : "not seen"}).`,
        `List shown: ${list}.`,
        lastAction ? `Last action: ${lastAction}${sent ? " (sent to the chat)" : ""}.` : "",
      ].filter(Boolean).join("\n")
    );
  }

  view.addEventListener("click", async (ev) => {
    const t = ev.target as HTMLElement;
    const actBtn = t.closest<HTMLButtonElement>("[data-act]");
    if (actBtn && !actBtn.disabled) return act(actBtn.dataset.act!);
    const nav = t.closest<HTMLElement>("[data-nav]");
    if (nav) {
      list = nav.dataset.nav!;
      return render();
    }
    const seenBtn = t.closest<HTMLElement>("[data-seen]");
    if (seenBtn) {
      const k = seenBtn.dataset.seen as ListKey;
      seen[k] = !seen[k];
      return render();
    }
    const more = t.closest<HTMLElement>("[data-more]");
    if (more) {
      allObjects.add(more.dataset.more!);
      return renderPane();
    }
    const grp = t.closest<HTMLElement>("[data-group]");
    if (grp) {
      const k = grp.dataset.group!;
      if (openGroups.has(k)) openGroups.delete(k);
      else openGroups.add(k);
      return renderPane();
    }
    if (t.closest('[data-k="toggle-marked"]')) {
      showMarked = !showMarked;
      return renderPane();
    }
    const markBtn = t.closest<HTMLButtonElement>("[data-mark]");
    if (markBtn) {
      // the card is redrawn in place, so the list does not jump while marking; it folds on the next visit
      const cardEl = markBtn.closest<HTMLElement>(".reading")!;
      const id = cardEl.dataset.id!;
      const mark = markBtn.dataset.mark as Mark;
      if (marks.get(id)?.mark === mark) marks.delete(id);
      else marks.set(id, { mark, note: marks.get(id)?.note ?? "" });
      cardEl.outerHTML = card(ov.readings.find((x) => x.id === id)!);
      view.querySelector<HTMLInputElement>(`.reading[data-id="${CSS.escape(id)}"] input.note`)?.focus();
      renderSide();
      renderDock();
      return state();
    }
    const row = t.closest<HTMLElement>("tr.task-row[data-task]");
    if (row) {
      const id = row.dataset.task!;
      if (expanded.has(id)) expanded.delete(id);
      else expanded.add(id);
      renderPane();
      return state();
    }
    const open = t.closest<HTMLElement>("[data-open]");
    if (open) {
      // hosts do not let the window open local files: the agent opens it
      const ok = await sendToChat(app, openReportPrompt(open.dataset.open!), view);
      say(ok ? "Asked the agent to open the report." : "Paste the instruction into the chat to open the report.");
      lastAction = "open report";
      return state();
    }
    const cp = t.closest<HTMLElement>("[data-copypath]");
    if (cp) {
      const ok = await copyText(cp.dataset.copypath!, view);
      say(ok ? "Path copied." : "Press Ctrl+C to copy the selected path.");
    }
  });
  view.addEventListener("keydown", (ev) => {
    const grp = (ev.target as HTMLElement).closest<HTMLElement>("[data-group]");
    if (grp && (ev.key === "Enter" || ev.key === " ")) {
      ev.preventDefault();
      grp.click();
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

  ready = true;
  render();
}
