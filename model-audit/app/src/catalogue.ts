import fs from "node:fs/promises";
import path from "node:path";

export type CatalogueTask = { task: string; tl: string; name: string; summary: string; groups: string[] };
export type Catalogue = { groups: { id: string; name: string }[]; tasks: CatalogueTask[] };

/** The package's tasks.json (written by tools/common/make_tasks_json.py). */
export async function loadCatalogue(packageRoot: string): Promise<Catalogue> {
  const file = path.join(packageRoot, "tasks.json");
  try {
    const data = JSON.parse(await fs.readFile(file, "utf-8")) as Catalogue;
    if (!Array.isArray(data.groups) || !Array.isArray(data.tasks)) throw new Error("groups or tasks missing");
    return data;
  } catch (e) {
    throw new Error(`tasks.json: ${(e as Error).message}`);
  }
}
