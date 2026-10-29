// The window: a run sheet at the top (what will run, what it will produce, where the results go, and the one Run button),
// then the checks by BIMGBPS section, then the outputs. After Run it says what happens next; the reports carry the results.
import type { App } from "@modelcontextprotocol/ext-apps";
import { sendToChat } from "./chat";
import { singleFlight } from "./logic/once";
import { joinPath, OUTPUTS, runPrompt, type OutputId } from "./logic/prompts";
import { groupsFor, sectionState, toggleSection, toggleTask } from "./logic/selection";
import { escapeHtml, plural } from "./ui/html";
import { navHtml } from "./ui/steps";

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
  let outputs = new Set<OutputId>(OUTPUTS.map((o) => o.id));
  let section = cat.sections[0]?.id ?? "";
  let search = "";
  let mode: "new" | "merge" = "new";
  let mergeRun = data.runs[0]?.name ?? "";

  const all = () => sel.size === cat.tasks.length;
  const existing = data.runs.map((r) => r.name);
  const inSection = (id: string) => cat.tasks.filter((t) => t.section === id);
  const picked = () => cat.tasks.filter((t) => sel.has(t.task));
  const chosenOutputs = () => OUTPUTS.filter((o) => outputs.has(o.id));
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
    <section class="runsheet" aria-label="This run">
      <dl>
        <dt>Checks</dt><dd data-k="sum-checks"></dd><a class="change" href="#checks" data-k="go-checks">Change</a>
        <dt>Outputs</dt><dd data-k="sum-outputs"></dd><a class="change" href="#outputs" data-k="go-outputs">Change</a>
        <dt>Results</dt><dd data-k="sum-results"></dd><span></span>
      </dl>
      <div class="go"><span class="why" data-k="why"></span>
        <button class="db pri" type="button" data-k="run" disabled>Run 0 checks</button></div>
    </section>
    <div class="part-head" id="checks"><h2>Checks</h2><p class="meta">By BIMGBPS section</p></div>
    <div class="layout">
      <div data-k="side"></div>
      <section class="pane">
        <div class="pane-head"><h3 data-k="title"></h3><button class="text-link" type="button" data-k="sec-toggle"></button></div>
        <p class="pane-why" data-k="pane-why"></p>
        <label class="search">
          <svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input data-k="search" type="search" placeholder="Search by number or name" autocomplete="off" />
        </label>
        <div data-k="list"></div>
      </section>
    </div>
    <div class="part-head" id="outputs"><h2>Outputs</h2><p class="meta">Written into the audit folder</p></div>
    <div class="outputs" data-k="outputs"></div>`;

  const $ = <T extends HTMLElement = HTMLElement>(k: string) => view.querySelector<T>(`[data-k="${k}"]`)!;

  function renderSheet() {
    const names = cat.sections.filter((s) => inSection(s.id).some((t) => sel.has(t.task))).map((s) => s.name);
    $("sum-checks").innerHTML = sel.size
      ? `${all() ? "Full audit · " : ""}${sel.size} of ${cat.tasks.length} <span class="dim">· ${escapeHtml(names.join(", "))}</span>`
      : '<span class="dim">None chosen yet</span>';
    const outs = chosenOutputs();
    $("sum-outputs").innerHTML = outs.length ? escapeHtml(outs.map((o) => o.label).join(" · ")) : '<span class="dim">None chosen</span>';
    if (mode === "new") {
      $("sum-results").innerHTML = `New audit <span class="mono">${escapeHtml(newName())}</span>` + (data.runs.length
        ? ` <span class="dim">·</span> <button class="text-link change" type="button" data-k="merge-on">Add to an earlier audit instead</button>`
        : "");
    } else {
      $("sum-results").innerHTML = `Add to <select data-k="pick-run" aria-label="Earlier audit">${data.runs.map((r) =>
        `<option value="${escapeHtml(r.name)}"${r.name === mergeRun ? " selected" : ""}>${escapeHtml(r.name)}</option>`).join("")}</select>` +
        ` <span class="dim">·</span> <button class="text-link change" type="button" data-k="merge-off">Back to a new audit</button>`;
    }
    const run = $<HTMLButtonElement>("run");
    run.textContent = `Run ${plural(sel.size, "check")}`;
    run.disabled = sel.size === 0 || outs.length === 0;
    $("why").textContent = sel.size === 0 ? "Choose the checks below, or Full audit."
      : outs.length === 0 ? "Choose at least one output below."
      : `Read-only on the model. Results go to ${joinPath(data.runsRoot, runName())}.`;
  }

  function renderSide() {
    const items = cat.sections.map((s) => {
      const n = inSection(s.id).filter((t) => sel.has(t.task)).length;
      return { id: s.id, label: s.name, count: `${n}/${inSection(s.id).length}`, tone: n ? ("unclear" as const) : ("muted" as const) };
    });
    const extra = `<div class="side-extra">
      <button type="button" class="side-item" data-quick="all">Full audit (all ${cat.tasks.length})</button>
      <button type="button" class="side-item" data-quick="clear">Clear</button></div>`;
    $("side").innerHTML = navHtml(items, section).replace("</nav>", `${extra}</nav>`);
  }

  function renderPane() {
    const s = cat.sections.find((x) => x.id === section)!;
    $("title").textContent = s.name;
    $("pane-why").textContent = `${s.clause} · ${SECTION_NOTE[section] ?? ""}`;
    $("sec-toggle").textContent = sectionState(sel, cat, section) === "all" ? "Clear section" : `Select all ${inSection(section).length}`;
    const q = search.trim().toLowerCase();
    const list = inSection(section).filter((t) => !q || [t.task, t.tl, t.name, t.summary].some((v) => v.toLowerCase().includes(q)));
    $("list").innerHTML = list.length
      ? list.map((t) => `<label class="task-line${sel.has(t.task) ? " sel" : ""}" data-task="${escapeHtml(t.task)}">
          <input type="checkbox" ${sel.has(t.task) ? "checked" : ""} />
          <span><span>${escapeHtml(t.name)}</span><br /><span class="sub">${escapeHtml(t.tl)} · ${escapeHtml(t.summary.replace(/^BIMGBPS\s*/, ""))}</span></span>
        </label>`).join("")
      : `<div class="empty"><b>No tasks match</b><span>Try another number or name.</span></div>`;
  }

  function renderOutputs() {
    $("outputs").innerHTML = OUTPUTS.map((o) => `<label class="output-line${outputs.has(o.id) ? " sel" : ""}" data-output="${o.id}">
        <input type="checkbox" ${outputs.has(o.id) ? "checked" : ""} /><b>${escapeHtml(o.label)}</b><span class="file">${escapeHtml(o.file)}</span>
        <span class="note">${escapeHtml(o.note)}</span></label>`).join("");
  }

  function render(pane = true) {
    renderSheet();
    renderSide();
    if (pane) renderPane();
    renderOutputs();
    onState(state());
  }

  function state() {
    return [
      "GBP Model Audit window: choose checks and outputs.",
      `Selected (${sel.size}): ${picked().map((t) => t.tl).join(", ") || "none"}.`,
      `Outputs: ${chosenOutputs().map((o) => o.label).join(", ") || "none"}.`,
      `Results: ${mode === "merge" ? `add to existing audit ${mergeRun}` : `new audit ${runName()}`}.`,
      `Section shown: ${section}.`,
    ].join("\n");
  }

  /** After Run: what happens next. The window has nothing else to do; the reports carry the results. */
  function renderNext(text: string, sent: boolean, box: Element | null) {
    const names = picked().map((t) => t.name);
    const dir = joinPath(data.runsRoot, runName());
    const outs = chosenOutputs();
    view.innerHTML = `
      <section class="runsheet" aria-label="This run">
        <dl>
          <dt>Checks</dt><dd>${escapeHtml(plural(names.length, "check"))} <span class="dim">· ${escapeHtml(names.slice(0, 5).join(", "))}${names.length > 5 ? ` +${names.length - 5} more` : ""}</span></dd><span></span>
          <dt>Outputs</dt><dd>${escapeHtml(outs.map((o) => o.label).join(" · "))}</dd><span></span>
          <dt>Results</dt><dd><span class="mono">${escapeHtml(dir)}</span></dd><span></span>
        </dl>
        <div class="go"><span class="why">${sent ? "Sent to the agent." : "Not sent: paste the instruction below into the chat."}</span>
          <button class="db pri" type="button" disabled>${sent ? "Sent" : "Not sent"}</button></div>
      </section>
      <div class="next">
        <div class="next-step now"><b>The agent reads the model and runs the checks</b>
          <p>${sent ? "Read-only, through the Revit MCP. Follow its progress in the chat; keep Revit open and idle (no dialogs)."
                    : "Paste the instruction below into the chat to start."}</p></div>
        <div class="next-step"><b>It writes your outputs into the audit folder</b>
          <ul>${outs.map((o) => `<li>${escapeHtml(o.label)} <span class="mono">${escapeHtml(o.file)}</span></li>`).join("")}</ul>
          <p>Values read off sheet images are listed in the reports as not checked by a person, with their crops.</p></div>
        ${sent ? `<p class="pane-why">Instruction sent: "${escapeHtml(text.slice(0, 80))}…" <button class="text-link" type="button" data-k="show-sent">Show</button></p>
                  <pre class="mono pane-why" data-k="sent-text" hidden>${escapeHtml(text)}</pre>` : ""}
      </div>`;
    if (box) view.append(box);
    view.querySelector('[data-k="show-sent"]')?.addEventListener("click", () => {
      const pre = view.querySelector<HTMLElement>('[data-k="sent-text"]')!;
      pre.hidden = !pre.hidden;
    });
    onState(`GBP Model Audit window: ${sent ? "instruction sent to the chat" : "instruction shown for copying"} ` +
            `(${plural(names.length, "check")}, outputs ${outs.map((o) => o.id).join(", ")}, run ${runName()}).`);
  }

  const run = singleFlight(async () => {
    const name = runName();
    const text = runPrompt({ tasks: picked().map((x) => x.task), groups: groupsFor(sel, cat), run: name,
                             runDir: joinPath(data.runsRoot, name), mode, all: all(), outputs: chosenOutputs().map((o) => o.id) });
    $<HTMLButtonElement>("run").disabled = true;
    const ok = await sendToChat(app, text, view);
    renderNext(text, ok, ok ? null : view.querySelector(".prompt-box"));
  });

  view.addEventListener("click", async (e) => {
    const t = e.target as HTMLElement;
    const jump = t.closest<HTMLElement>('[data-k="go-checks"], [data-k="go-outputs"]');
    if (jump) {
      e.preventDefault();
      view.querySelector(jump.dataset.k === "go-checks" ? "#checks" : "#outputs")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
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
    const out = t.closest<HTMLElement>("[data-output]");
    if (out && t.tagName === "INPUT") {
      const id = out.dataset.output as OutputId;
      outputs = new Set(outputs);
      if (outputs.has(id)) outputs.delete(id);
      else outputs.add(id);
      return render(false);
    }
    if (t.closest('[data-k="merge-on"]')) {
      mode = "merge";
      return render(false);
    }
    if (t.closest('[data-k="merge-off"]')) {
      mode = "new";
      return render(false);
    }
    if (t.closest('[data-k="run"]') && sel.size && outputs.size) return run();
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
