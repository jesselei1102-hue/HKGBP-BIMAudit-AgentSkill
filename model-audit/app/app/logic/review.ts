// What the review window still needs before the reports: each list looked at once, every sheet reading marked.
import type { ReviewCounts, Reviewed } from "../../src/types";

export type Seen = { failures: boolean; check_yourself: boolean; inputs: boolean };
export type ReviewInput = {
  failures: number;
  checkYourself: number;
  inputs: number;          // -INPUT checks + data warnings
  readingsLeft: number;    // not marked yet
  readingsWrong: number;   // marked Wrong
  seen: Seen;
  reportsReady: boolean;
};
export type ReviewState = {
  done: { failures: boolean; check_yourself: boolean; inputs: boolean; readings: boolean };
  doneCount: number;
  dock: "partial" | "wrong" | "ready" | "reports";
  label: string;
};

/** An empty list counts as looked at; a reading marked Wrong keeps the readings open (they go back for re-reading). */
export function reviewState(i: ReviewInput): ReviewState {
  const done = {
    failures: i.failures === 0 || i.seen.failures,
    check_yourself: i.checkYourself === 0 || i.seen.check_yourself,
    inputs: i.inputs === 0 || i.seen.inputs,
    readings: i.readingsLeft === 0 && i.readingsWrong === 0,
  };
  const doneCount = Object.values(done).filter(Boolean).length;
  if (i.reportsReady) return { done, doneCount, dock: "reports", label: "Reports ready" };
  if (i.readingsWrong > 0)
    return { done, doneCount, dock: "wrong",
             label: `${i.readingsWrong} ${i.readingsWrong === 1 ? "reading" : "readings"} marked wrong` };
  if (doneCount === 4) return { done, doneCount, dock: "ready", label: "All reviewed" };
  return { done, doneCount, dock: "partial", label: `${doneCount} of 4 reviewed` };
}

/** Ticks from a saved review, kept only for lists that still hold as many items (an audit added to since starts unticked). */
export function restoreSeen(reviewed: Reviewed | undefined, counts: ReviewCounts | undefined, now: ReviewCounts): Seen {
  const keep = (k: keyof Seen) => !!reviewed?.[k] && !!counts && counts[k] === now[k];
  return { failures: keep("failures"), check_yourself: keep("check_yourself"), inputs: keep("inputs") };
}
