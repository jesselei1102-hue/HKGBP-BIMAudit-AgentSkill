// Which tasks are ticked. A task can belong to several groups; ticking it once ticks it everywhere.

export type SelectionCatalogue = { groups: { id: string }[]; tasks: { task: string; groups: string[] }[] };

const inGroup = (cat: SelectionCatalogue, group: string) =>
  cat.tasks.filter((t) => t.groups.includes(group)).map((t) => t.task);

export function toggleTask(sel: Set<string>, task: string): Set<string> {
  const next = new Set(sel);
  if (next.has(task)) next.delete(task);
  else next.add(task);
  return next;
}

/** Select the whole group, or clear it when it is already fully selected. */
export function toggleGroup(sel: Set<string>, cat: SelectionCatalogue, group: string): Set<string> {
  const tasks = inGroup(cat, group);
  const next = new Set(sel);
  const all = tasks.every((t) => next.has(t));
  for (const t of tasks) {
    if (all) next.delete(t);
    else next.add(t);
  }
  return next;
}

/** Groups that have at least one selected task, in catalogue order. */
export function groupsFor(sel: Set<string>, cat: SelectionCatalogue): string[] {
  return cat.groups.map((g) => g.id).filter((g) => inGroup(cat, g).some((t) => sel.has(t)));
}

export function groupState(sel: Set<string>, cat: SelectionCatalogue, group: string): "all" | "some" | "none" {
  const tasks = inGroup(cat, group);
  const n = tasks.filter((t) => sel.has(t)).length;
  return n === 0 ? "none" : n === tasks.length ? "all" : "some";
}
