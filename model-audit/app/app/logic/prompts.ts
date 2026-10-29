// The instruction the window sends to the chat. Plain text in English; the agent follows RUN.md.

export type OutputId = "bim" | "ap" | "excel";

/** What the operator can ask for before the run, in the order the instruction names them. */
export const OUTPUTS: { id: OutputId; label: string; file: string; note: string }[] = [
  { id: "bim", label: "BIM team report", file: "report-bim.html",
    note: "Every failing object with where it is, its Revit ID and the fix; copy IDs for Select by ID or a line for the agent." },
  { id: "ap", label: "AP / client report", file: "report-ap.html",
    note: "Whether it can be submitted, the decisions only the AP can make, and the information to supply." },
  { id: "excel", label: "Excel issue list", file: "issues.xlsx",
    note: "One row per object with its Revit ID and fix, to filter and assign." },
];

export type RunRequest = {
  tasks: string[];
  groups: string[];
  run: string;
  runDir: string;
  mode: "new" | "merge";
  all: boolean;
  outputs: OutputId[];
};

const short = (t: string) => t.replace(/^AUD-/, "");

/** runsRoot + folder name, using the root's own separator. */
export function joinPath(root: string, name: string): string {
  const sep = root.includes("\\") ? "\\" : "/";
  return root.replace(/[\\/]+$/, "") + sep + name;
}

export function outputsLine(ids: OutputId[]): string {
  return OUTPUTS.filter((o) => ids.includes(o.id)).map((o) => `${o.label} (${o.file})`).join(", ");
}

function build(outputs: OutputId[]): string {
  return (
    `Then build these outputs straight away, with no review step (RUN.md §6b step 4): ${outputsLine(outputs)}. ` +
    "Tell me where they are when they are ready."
  );
}

export function runPrompt(r: RunRequest): string {
  if (r.all && r.mode === "new")
    return (
      "Run a full Model Audit on the open model. Follow model-audit/RUN.md §6b. Read-only. " +
      `Run folder: ${r.runDir}. Put every group's analysis JSON in that folder. ` +
      build(r.outputs)
    );
  return (
    `Run these Model Audit tasks on the open model: ${r.tasks.map(short).join(", ")} (groups ${r.groups.join(", ")}). ` +
    "Follow model-audit/RUN.md §6c: extract only what each group table lists, run each group's analyser with --tasks. Read-only. " +
    `Run folder: ${r.runDir}. ` +
    (r.mode === "merge" ? "Merge the results into the existing audit in that folder with build_results.py --update (RUN.md §6c step 4). " : "") +
    build(r.outputs)
  );
}
