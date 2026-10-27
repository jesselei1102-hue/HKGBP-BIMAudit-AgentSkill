// Shared shapes between the server (overview, gate) and the window.

export type Status = "PASS" | "FAIL" | "UNCLEAR" | "N/A";

export type Check = {
  id: string;
  task: string;
  group: string;
  item: string;
  object: string;
  expected: string;
  actual: string;
  status: Status;
  cite: string;
  fix: string;
};

/** A value read off a sheet. `crop` is a path inside the run folder, or null when there is no usable crop. */
export type Reading = {
  id: string;
  group: string;
  key: string;
  sheet: string;
  item: string;
  value: string;
  finding: string;
  confidence: string;
  note: string;
  crop: string | null;
};

export type TaskRow = { task: string; tl: string; name: string; groups: string[]; counts: Record<Status, number> };

export type Mark = "ok" | "wrong" | "none";
export type GateMode = "confirmed" | "unreviewed";
export type GateReading = {
  id: string;
  group: string;
  key: string;
  sheet: string;
  item: string;
  value: string;
  mark: Mark;
  note: string;
};
export type GateRecord = { mode: GateMode; saved: string; readings: GateReading[] };

export type Overview = {
  run: string;
  project: string;
  groups: string[];
  partial: boolean;
  tasks: TaskRow[];
  checks: Check[];
  readings: Reading[];
  inputs: Check[];
  warnings: string[];
  reports: { bim: string | null; ap: string | null; groups: string[] };
  /** True when the run's reports are newer than every analysis file and the review: the reports show these results. */
  reportsCurrent: boolean;
  gate: GateRecord | null;
  counts: { checks: number; fail: number; unclear: number; readings: number };
};
