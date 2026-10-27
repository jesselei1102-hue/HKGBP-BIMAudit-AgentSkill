// Reading marks in the window. A mark belongs to the value and sheet the operator saw, so a re-run that changes
// either one leaves the reading unmarked (in the window and when the server saves the review).
import type { Mark } from "../../src/types";

type Seen = { id: string; value: string; sheet: string };
type Saved = Seen & { mark: Mark; note: string };
export type MarkState = { mark: Mark; note: string };

/** Marks from an earlier gate-confirmation.json that still match the current readings. */
export function preloadMarks(readings: Seen[], saved: Saved[]): Map<string, MarkState> {
  const now = new Map(readings.map((r) => [r.id, r]));
  const out = new Map<string, MarkState>();
  for (const s of saved) {
    const r = now.get(s.id);
    if (s.mark !== "none" && r && r.value === s.value && r.sheet === s.sheet) out.set(s.id, { mark: s.mark, note: s.note });
  }
  return out;
}

/** The save_gate marks argument: each mark with the value and sheet shown to the operator. */
export function markPayload(marks: Map<string, MarkState>, readings: Seen[]) {
  const shown = new Map(readings.map((r) => [r.id, r]));
  return Object.fromEntries(
    [...marks]
      .filter(([id]) => shown.has(id))
      .map(([id, m]) => [id, { mark: m.mark, note: m.note, value: shown.get(id)!.value, sheet: shown.get(id)!.sheet }])
  );
}
