// The review list shows one row per task and check item ("Door marks on all doors" on 4 plans is one row),
// with the objects it covers and the distinct fixes underneath.
import type { Check, Status } from "../../src/types";

export type CheckGroup = {
  key: string;
  task: string;
  item: string;
  status: Status;
  objects: { object: string; actual: string }[];
  fixes: string[];
  checks: Check[];
};

/** Groups by (task, item); groups follow `taskOrder` (catalogue order), unknown tasks last, items in first-seen order. */
export function groupChecks(checks: Check[], taskOrder: string[]): CheckGroup[] {
  const groups = new Map<string, CheckGroup>();
  for (const c of checks) {
    const key = `${c.task}|${c.item}`;
    let g = groups.get(key);
    if (!g) {
      g = { key, task: c.task, item: c.item, status: c.status, objects: [], fixes: [], checks: [] };
      groups.set(key, g);
    }
    g.objects.push({ object: c.object, actual: c.actual });
    if (c.fix && !g.fixes.includes(c.fix)) g.fixes.push(c.fix);
    g.checks.push(c);
  }
  const rank = (t: string) => (taskOrder.includes(t) ? taskOrder.indexOf(t) : taskOrder.length);
  return [...groups.values()]
    .map((g, i) => ({ g, i }))
    .sort((a, b) => rank(a.g.task) - rank(b.g.task) || a.i - b.i)
    .map(({ g }) => g);
}
