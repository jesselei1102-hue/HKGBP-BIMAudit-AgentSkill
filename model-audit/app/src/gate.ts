import fs from "node:fs/promises";
import path from "node:path";
import type { Catalogue } from "./catalogue.js";
import { readOverview } from "./overview.js";
import { resolveInside } from "./paths.js";
import type { GateMode, GateRecord, Mark, ReviewCounts, Reviewed } from "./types.js";

/** The review cannot be saved as asked; the message says why. */
export class GateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GateError";
  }
}

const MARKS: Mark[] = ["ok", "wrong", "none"];

/**
 * Write <run>/gate-confirmation.json. The readings are the ones on disk now (the agent may have re-run the analysis
 * since the window opened); marks for readings that no longer exist are ignored, missing marks count as "none",
 * and a mark sent with a value or sheet that differs from the reading on disk counts as "none" (the operator did not
 * see the current value).
 * "confirmed" needs every reading marked ok.
 */
export async function saveGate(
  runsRoot: string,
  run: string,
  catalogue: Catalogue,
  marks: Record<string, { mark: Mark; note?: string; value?: string; sheet?: string }>,
  mode: GateMode,
  now: () => Date = () => new Date(),
  reviewed?: Reviewed,
  counts?: ReviewCounts
): Promise<{ path: string; record: GateRecord }> {
  if (mode !== "confirmed" && mode !== "unreviewed") throw new GateError(`Unknown mode: ${String(mode)}`);
  const { readings } = await readOverview(runsRoot, run, catalogue);
  const record: GateRecord = {
    mode,
    saved: now().toISOString(),
    readings: readings.map((r) => {
      const m = marks[r.id];
      const seen = m && (m.value === undefined || m.value === r.value) && (m.sheet === undefined || m.sheet === r.sheet);
      const mark = m && seen && MARKS.includes(m.mark) ? m.mark : "none";
      return { id: r.id, group: r.group, key: r.key, sheet: r.sheet, item: r.item, value: r.value, mark,
               note: mark === "wrong" ? String(m?.note ?? "") : "" };
    }),
  };
  if (reviewed) record.reviewed = reviewed;
  if (counts) record.reviewed_counts = counts;
  if (mode === "confirmed") {
    const left = record.readings.filter((r) => r.mark !== "ok").map((r) => r.id);
    if (left.length)
      throw new GateError(`${left.length} ${left.length === 1 ? "reading is" : "readings are"} not marked ok: ${left.join(", ")}`);
  }
  const file = path.join(resolveInside(runsRoot, run), "gate-confirmation.json");
  await fs.writeFile(file + ".tmp", JSON.stringify(record, null, 1), "utf-8");
  await fs.rename(file + ".tmp", file);
  return { path: file, record };
}
