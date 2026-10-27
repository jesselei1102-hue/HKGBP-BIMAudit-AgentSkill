// Which tasks are ticked. The window lists tasks by BIMGBPS section; the groups (which analysers run) follow from
// the ticked tasks. A task can belong to several groups.

export type SelectionCatalogue = { groups: { id: string }[]; tasks: { task: string; groups: string[]; section?: string }[] };

const inGroup = (cat: SelectionCatalogue, group: string) =>
  cat.tasks.filter((t) => t.groups.includes(group)).map((t) => t.task);
const inSection = (cat: SelectionCatalogue, section: string) =>
  cat.tasks.filter((t) => t.section === section).map((t) => t.task);

function toggleAll(sel: Set<string>, tasks: string[]): Set<string> {
  const next = new Set(sel);
  const all = tasks.every((t) => next.has(t));
  for (const t of tasks) {
    if (all) next.delete(t);
    else next.add(t);
  }
  return next;
}

function stateOf(sel: Set<string>, tasks: string[]): "all" | "some" | "none" {
  const n = tasks.filter((t) => sel.has(t)).length;
  return n === 0 ? "none" : n === tasks.length ? "all" : "some";
}

/** Select a whole BIMGBPS section, or clear it when it is already fully selected. */
export function toggleSection(sel: Set<string>, cat: SelectionCatalogue, section: string): Set<string> {
  return toggleAll(sel, inSection(cat, section));
}

export function sectionState(sel: Set<string>, cat: SelectionCatalogue, section: string): "all" | "some" | "none" {
  return stateOf(sel, inSection(cat, section));
}

export function toggleTask(sel: Set<string>, task: string): Set<string> {
  const next = new Set(sel);
  if (next.has(task)) next.delete(task);
  else next.add(task);
  return next;
}

/** Select the whole group, or clear it when it is already fully selected. */
export function toggleGroup(sel: Set<string>, cat: SelectionCatalogue, group: string): Set<string> {
  return toggleAll(sel, inGroup(cat, group));
}

/** Groups that have at least one selected task, in catalogue order. */
export function groupsFor(sel: Set<string>, cat: SelectionCatalogue): string[] {
  return cat.groups.map((g) => g.id).filter((g) => inGroup(cat, g).some((t) => sel.has(t)));
}

export function groupState(sel: Set<string>, cat: SelectionCatalogue, group: string): "all" | "some" | "none" {
  return stateOf(sel, inGroup(cat, group));
}
