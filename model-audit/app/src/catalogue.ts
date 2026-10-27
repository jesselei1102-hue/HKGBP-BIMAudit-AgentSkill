import fs from "node:fs/promises";
import path from "node:path";

/** `section`: the BIMGBPS section the window lists it under; `groups`: the analysers that run it. */
export type CatalogueTask = { task: string; tl: string; name: string; summary: string; groups: string[]; section: string };
export type Catalogue = {
  sections: { id: string; name: string; clause: string }[];
  groups: { id: string; name: string }[];
  tasks: CatalogueTask[];
};

/** The package's tasks.json (written by tools/common/make_tasks_json.py). */
export async function loadCatalogue(packageRoot: string): Promise<Catalogue> {
  const file = path.join(packageRoot, "tasks.json");
  try {
    const data = JSON.parse(await fs.readFile(file, "utf-8")) as Catalogue;
    if (!Array.isArray(data.sections) || !Array.isArray(data.groups) || !Array.isArray(data.tasks))
      throw new Error("sections, groups or tasks missing");
    return data;
  } catch (e) {
    throw new Error(`tasks.json: ${(e as Error).message}`);
  }
}
