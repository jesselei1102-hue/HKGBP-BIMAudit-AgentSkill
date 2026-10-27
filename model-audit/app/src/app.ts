import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { loadCatalogue } from "./catalogue.js";
import type { Config } from "./config.js";
import { saveGate } from "./gate.js";
import { readOverview } from "./overview.js";
import { resolveInside } from "./paths.js";
import { listRuns, newRunName } from "./runs.js";

/** Also the `name` in package.json. Used in the server name and the ui:// address. */
export const APP_NAME = "gbp-audit";

const MAX_CROP = 5 * 1024 * 1024;
const IMAGE_TYPES: Record<string, string> = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg" };

/**
 * Hosts cache UI resources by URI (Claude desktop keeps them across sessions), so the URI carries
 * a content hash: every rebuilt app.html gets a new URI and is fetched fresh after a reconnect.
 */
export async function versionedResourceUri(appName: string, htmlPath: string): Promise<string> {
  try {
    const html = await fs.readFile(htmlPath);
    const hash = createHash("sha256").update(html).digest("hex").slice(0, 12);
    return `ui://${appName}/app-${hash}.html`;
  } catch {
    return `ui://${appName}/app.html`;
  }
}

function result(data: Record<string, unknown>) {
  return { content: [{ type: "text" as const, text: JSON.stringify(data) }], structuredContent: data };
}

function failure(message: string, data: Record<string, unknown> = {}) {
  return { content: [{ type: "text" as const, text: message }], structuredContent: { ...data, error: message }, isError: true };
}

/** Local date as YYYY-MM-DD (run folder names follow the operator's calendar, not UTC). */
function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** `htmlPath`: the built window (build/app/app.html next to the running server unless given, e.g. by tests). */
export async function registerApp(
  server: McpServer,
  config: Config,
  htmlPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "app", "app.html")
): Promise<void> {
  const { packageRoot, runsRoot } = config;
  const resourceUri = await versionedResourceUri(APP_NAME, htmlPath);

  registerAppTool(
    server,
    "choose_checks",
    {
      title: "GBP Model Audit · Choose checks",
      description:
        "[MCP Apps] Opens the GBP Model Audit window to choose which checks to run. " +
        "Call it when the operator asks for a GBP model audit; then follow the instruction the window sends.",
      inputSchema: {},
      _meta: { ui: { resourceUri } },
    },
    async () => {
      const [catalogue, runs] = [await loadCatalogue(packageRoot), await listRuns(runsRoot)];
      const day = today();
      return result({ view: "choose", catalogue, runs, runsRoot, packageRoot, today: day,
                      suggested: newRunName(day, [], true, runs.map((r) => r.name)) });
    }
  );

  registerAppTool(
    server,
    "show_overview",
    {
      title: "GBP Model Audit · Overview",
      description:
        "[MCP Apps] Shows the results of one audit run for review before the reports are built, and the report links " +
        "afterwards. Call it after the analysis (then wait for the operator's confirmation) and again after the reports.",
      inputSchema: { run: z.string().describe("Audit folder name under the runs folder, e.g. audit-2026-10-27-full.") },
      _meta: { ui: { resourceUri } },
    },
    async ({ run }) => {
      try {
        const catalogue = await loadCatalogue(packageRoot);
        const overview = await readOverview(runsRoot, run, catalogue);
        return result({ view: "overview", overview, sections: catalogue.sections, runsRoot });
      } catch (e) {
        return failure((e as Error).message, { view: "overview", runsRoot });
      }
    }
  );

  // Called by the window only.
  server.registerTool(
    "get_crop",
    {
      title: "GBP Model Audit · Crop image",
      description: "One crop image of a sheet reading, as base64 (window only).",
      inputSchema: { run: z.string(), file: z.string().describe("Path inside the run folder.") },
      _meta: { ui: { visibility: ["app"] } },
    },
    async ({ run, file }) => {
      try {
        const mime = IMAGE_TYPES[path.extname(file).toLowerCase()];
        if (!mime) return failure("Only png or jpg crops can be shown.");
        const abs = resolveInside(resolveInside(runsRoot, run), file);
        const stat = await fs.stat(abs);
        if (stat.size > MAX_CROP) return failure("The crop is larger than 5 MB.");
        return result({ mime, base64: (await fs.readFile(abs)).toString("base64") });
      } catch (e) {
        return failure((e as Error).message);
      }
    }
  );

  server.registerTool(
    "save_gate",
    {
      title: "GBP Model Audit · Save review",
      description: "Saves the reading review of one audit run to gate-confirmation.json (window only).",
      inputSchema: {
        run: z.string(),
        marks: z.record(
          z.object({
            mark: z.enum(["ok", "wrong", "none"]),
            note: z.string().optional(),
            value: z.string().optional().describe("The value the operator saw; a mismatch with the run counts as unmarked."),
            sheet: z.string().optional(),
          })
        ),
        mode: z.enum(["confirmed", "unreviewed"]),
      },
      _meta: { ui: { visibility: ["app"] } },
    },
    async ({ run, marks, mode }) => {
      try {
        const saved = await saveGate(runsRoot, run, await loadCatalogue(packageRoot), marks, mode);
        return result(saved);
      } catch (e) {
        return failure((e as Error).message);
      }
    }
  );

  registerAppResource(server, resourceUri, resourceUri, { mimeType: RESOURCE_MIME_TYPE }, async () => ({
    contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: await fs.readFile(htmlPath, "utf-8") }],
  }));
}
