import fs from "node:fs/promises";
import path from "node:path";

export type RunInfo = { name: string; groups: string[]; partial: boolean; hasReports: boolean; modified: string };
export type ResultFile = { kind: "g1" | "full" | "partial"; group: string };

/** Same as PARTIAL_NAME in tools/common/tasks.py: the task part of a --tasks result such as G2_S10-S13.json. */
const PARTIAL = /^G([2-5])_(([SVA]\d\d|A1)(-([SVA]\d\d|A1))*)\.json$/;
const FULL = /^G([2-5])_analysis_.*\.json$/;
const G1 = /^C14_analysis_.*\.json$/;

/** What an analysis file in a run folder is, from its name; null for anything else (including *.prev.json). */
export function classify(file: string): ResultFile | null {
  if (file.endsWith(".prev.json")) return null;
  if (G1.test(file)) return { kind: "g1", group: "G1" };
  let m = FULL.exec(file);
  if (m) return { kind: "full", group: "G" + m[1] };
  m = PARTIAL.exec(file);
  if (m) return { kind: "partial", group: "G" + m[1] };
  return null;
}

/** Audit folders directly under the runs root that hold analysis results, newest first. */
export async function listRuns(runsRoot: string): Promise<RunInfo[]> {
  let entries;
  try {
    entries = await fs.readdir(runsRoot, { withFileTypes: true });
  } catch {
    return [];
  }
  const runs: (RunInfo & { t: number })[] = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const dir = path.join(runsRoot, e.name);
    const files = await fs.readdir(dir);
    const kinds = files.map(classify).filter((k): k is ResultFile => k !== null);
    if (!kinds.length && !files.includes("audit-results.json")) continue;
    const groups = [...new Set(kinds.map((k) => k.group))].sort();
    const partial = groups.some((g) => !kinds.some((k) => k.group === g && k.kind !== "partial"));
    const t = (await fs.stat(dir)).mtimeMs;
    runs.push({ name: e.name, groups, partial, hasReports: files.includes("report-bim.html") || files.includes("report-ap.html"),
                modified: new Date(t).toISOString(), t });
  }
  return runs.sort((a, b) => b.t - a.t).map(({ t: _t, ...r }) => r);
}

/** audit-<today>-full, audit-<today>-s10-s13, or audit-<today>-<n>tasks; -2, -3 … when the name is taken. */
export function newRunName(today: string, tasks: string[], all: boolean, existing: string[]): string {
  const ids = tasks.map((t) => t.replace(/^AUD-/, "").toLowerCase());
  const base = `audit-${today}-${all ? "full" : ids.length > 4 ? `${ids.length}tasks` : ids.join("-")}`;
  let name = base;
  for (let i = 2; existing.includes(name); i++) name = `${base}-${i}`;
  return name;
}
