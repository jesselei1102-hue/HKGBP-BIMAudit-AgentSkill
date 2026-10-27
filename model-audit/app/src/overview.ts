import { existsSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import type { Catalogue } from "./catalogue.js";
import { isInside, resolveInside } from "./paths.js";
import { classify, type ResultFile } from "./runs.js";
import type { Check, GateRecord, Overview, Reading, Status, TaskRow } from "./types.js";

/** A run that cannot be read; the message names the file. */
export class OverviewError extends Error {
  constructor(public file: string, reason: string) {
    super(`${file}: ${reason}`);
    this.name = "OverviewError";
  }
}

type Json = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

const STATUSES: Status[] = ["PASS", "FAIL", "UNCLEAR", "N/A"];
const str = (v: unknown) => (v === null || v === undefined ? "" : String(v));

/** Same mapping as build_results.STATUS: APPLICABLE and anything unknown cannot be decided. */
function status(v: unknown): Status {
  const s = str(v).toUpperCase();
  return (STATUSES as string[]).includes(s) ? (s as Status) : "UNCLEAR";
}

async function readJson(dir: string, file: string): Promise<Json> {
  try {
    return JSON.parse(await fs.readFile(path.join(dir, file), "utf-8"));
  } catch (e) {
    throw new OverviewError(file, (e as Error).message);
  }
}

function groupChecks(data: Json, group: string): Check[] {
  return (data.checks ?? []).map((c: Json) => ({
    id: str(c.id), task: str(c.task), group, item: str(c.item), object: str(c.object), expected: str(c.expected),
    actual: str(c.actual), status: status(c.status), cite: str(c.cite), fix: str(c.fix),
  }));
}

/** G1 (S14) results are per room, not per check: one check per assessed room, pending rooms cannot be decided. */
function s14Checks(data: Json): Check[] {
  const base = { task: "AUD-S14", group: "G1", item: "Lighting and ventilation" };
  const where = (r: Json) => `${str(r.name)} ${str(r.number)} · ${str(r.level)}`;
  const out: Check[] = (data.rooms_included ?? []).map((r: Json) => ({
    ...base, id: `S14-R${r.id}`, object: where(r),
    expected: `light ≥ ${str(r.req_light_sqm)} m², vent ≥ ${str(r.req_vent_sqm)} m²`,
    actual: `light ${str(r.act_light_sqm)} m², vent ${str(r.act_vent_sqm)} m²`,
    status: status(r.status), cite: str(r.rule_cite), fix: "",
  }));
  for (const r of [...(data.rooms_pending ?? []), ...(data.rooms_no_area ?? [])]) {
    out.push({ ...base, id: `S14-R${r.id}`, object: where(r), expected: "rule decided", actual: str(r.classification),
               status: "UNCLEAR", cite: "", fix: str(r.classification_reason) || "Room has no area" });
  }
  return out;
}

/** A crop path from an analysis file, as a path inside the run, or null if it is elsewhere or missing. */
function cropRef(runDir: string, crop: unknown): string | null {
  const c = str(crop);
  if (!c) return null;
  const isAbs = path.isAbsolute(c) || path.win32.isAbsolute(c);
  const abs = isAbs ? c : path.resolve(runDir, c);
  if (!isInside(runDir, abs) || !existsSync(abs)) return null;
  return path.relative(runDir, abs).split(path.sep).join("/");
}

function readings(data: Json, group: string, runDir: string): Reading[] {
  return (data.readings ?? []).map((r: Json) => ({
    id: `${group}:${str(r.key)}`, group, key: str(r.key), sheet: str(r.sheet), item: str(r.item), value: str(r.value),
    finding: str(r.finding), confidence: str(r.confidence), note: str(r.note), crop: cropRef(runDir, r.crop),
  }));
}

async function reportFiles(runDir: string): Promise<Overview["reports"]> {
  const top = await fs.readdir(runDir);
  const assets = existsSync(path.join(runDir, "assets")) ? await fs.readdir(path.join(runDir, "assets")) : [];
  const isGroup = (f: string) => f.startsWith("GBP_") && f.endsWith(".html");
  return {
    bim: top.includes("report-bim.html") ? "report-bim.html" : null,
    ap: top.includes("report-ap.html") ? "report-ap.html" : null,
    groups: [...top.filter(isGroup), ...assets.filter(isGroup).map((f) => `assets/${f}`)],
  };
}

/** Everything the overview window shows for one audit run folder under the runs root. */
export async function readOverview(runsRoot: string, run: string, catalogue: Catalogue): Promise<Overview> {
  const runDir = resolveInside(runsRoot, run);
  let files: string[];
  try {
    files = (await fs.readdir(runDir)).sort();
  } catch {
    throw new OverviewError(run, "the audit folder does not exist");
  }
  const kinds = new Map<string, ResultFile>();
  for (const f of files) {
    const k = classify(f);
    if (k) kinds.set(f, k);
  }
  const hasFull = (g: string) => [...kinds.values()].some((k) => k.group === g && k.kind !== "partial");

  const checks: Check[] = [];
  const allReadings: Reading[] = [];
  const warnings: string[] = [];
  const groups = new Set<string>();
  let project = "";
  let partial = false;
  for (const [file, k] of kinds) {
    if (k.kind === "partial" && hasFull(k.group)) continue;
    const data = await readJson(runDir, file);
    groups.add(k.group);
    partial ||= k.kind === "partial";
    project ||= str(data.project_info?.project_name);
    checks.push(...(k.kind === "g1" ? s14Checks(data) : groupChecks(data, k.group)));
    allReadings.push(...readings(data, k.group, runDir));
    for (const w of data.summary?.data_quality_warnings ?? []) if (!warnings.includes(w)) warnings.push(str(w));
  }

  const meta = new Map(catalogue.tasks.map((t, i) => [t.task, { ...t, i }]));
  const tasks: TaskRow[] = [...new Set(checks.map((c) => c.task))]
    .sort((a, b) => (meta.get(a)?.i ?? 999) - (meta.get(b)?.i ?? 999))
    .map((task) => {
      const counts = { PASS: 0, FAIL: 0, UNCLEAR: 0, "N/A": 0 } as Record<Status, number>;
      for (const c of checks) if (c.task === task) counts[c.status]++;
      const m = meta.get(task);
      return { task, tl: m?.tl ?? task, name: m?.name ?? task, groups: m?.groups ?? [], counts };
    });

  const gate = files.includes("gate-confirmation.json")
    ? ((await readJson(runDir, "gate-confirmation.json")) as GateRecord)
    : null;

  const mtime = async (f: string) => (await fs.stat(path.join(runDir, f))).mtimeMs;
  const reports = await reportFiles(runDir);
  const made = [reports.bim, reports.ap].filter((f): f is string => !!f);
  const inputs = [...kinds.keys(), ...(gate ? ["gate-confirmation.json"] : [])];
  const reportsCurrent =
    made.length > 0 &&
    Math.min(...(await Promise.all(made.map(mtime)))) > Math.max(0, ...(await Promise.all(inputs.map(mtime))));

  return {
    run, project, groups: [...groups].sort(), partial, tasks, checks, readings: allReadings,
    inputs: checks.filter((c) => c.id.endsWith("-INPUT")), warnings, reports, reportsCurrent, gate,
    counts: { checks: checks.length, fail: checks.filter((c) => c.status === "FAIL").length,
              unclear: checks.filter((c) => c.status === "UNCLEAR").length, readings: allReadings.length },
  };
}
