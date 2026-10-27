// The instructions the window sends to the chat. Plain text in English; the agent follows RUN.md.

export type RunRequest = {
  tasks: string[];
  groups: string[];
  run: string;
  runDir: string;
  mode: "new" | "merge";
  all: boolean;
};

const short = (t: string) => t.replace(/^AUD-/, "");
const thenOverview = (run: string) =>
  `After the analysis, call show_overview with run "${run}" and wait for my confirmation before building the reports.`;

/** runsRoot + folder name, using the root's own separator. */
export function joinPath(root: string, name: string): string {
  const sep = root.includes("\\") ? "\\" : "/";
  return root.replace(/[\\/]+$/, "") + sep + name;
}

export function runPrompt(r: RunRequest): string {
  if (r.all && r.mode === "new")
    return (
      "Run a full Model Audit on the open model. Follow model-audit/RUN.md §6b. Read-only. " +
      `Run folder: ${r.runDir}. Put every group's analysis JSON in that folder. ` +
      thenOverview(r.run)
    );
  return (
    `Run these Model Audit tasks on the open model: ${r.tasks.map(short).join(", ")} (groups ${r.groups.join(", ")}). ` +
    "Follow model-audit/RUN.md §6c: extract only what each group table lists, run each group's analyser with --tasks. Read-only. " +
    `Run folder: ${r.runDir}. ` +
    (r.mode === "merge"
      ? "Merge the results into the existing audit in that folder with build_results.py --update (RUN.md §6c step 4) " +
        "before calling show_overview, so the overview shows the new readings. "
      : "") +
    thenOverview(r.run)
  );
}

export function confirmPrompt(run: string): string {
  return (
    `Gate confirmed for run "${run}" (gate-confirmation.json saved). ` +
    `Build the reports per RUN.md §6b steps 3-4, then call show_overview with run "${run}" again.`
  );
}

export function rereadPrompt(run: string, wrong: { id: string; sheet: string; item: string; note: string }[]): string {
  const lines = wrong.map((w) => `- ${w.id} (${w.sheet}, ${w.item}): ${w.note.trim() || "no note"}`);
  return (
    `These readings in run "${run}" were marked wrong:\n${lines.join("\n")}\n` +
    `Re-read them from the sheets, re-run the analysis for the affected groups, then call show_overview with run "${run}" again.`
  );
}

/** Hosts do not let the window open local files, so the agent opens the report. */
export function openReportPrompt(path: string): string {
  return `Open this report in my default browser: ${path}`;
}

export function unreviewedPrompt(run: string, unchecked: number): string {
  return (
    `Build the reports for run "${run}" without a full reading review ` +
    `(${unchecked} ${unchecked === 1 ? "reading" : "readings"} not checked; recorded in gate-confirmation.json). ` +
    `Follow RUN.md §6b steps 3-4, then call show_overview with run "${run}" again.`
  );
}
