import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadCatalogue } from "./catalogue.js";
import type { Config } from "./config.js";
import { listRuns, newRunName } from "./runs.js";

/** Also the `name` in package.json. Used in the server name and the ui:// address. */
export const APP_NAME = "gbp-audit";

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
        "[MCP Apps] Opens the GBP Model Audit window, where the operator chooses the checks and the outputs " +
        "(BIM team report, AP / client report, Excel issue list). Call it when the operator asks for a GBP model audit; " +
        "then follow the instruction the window sends.",
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

  registerAppResource(server, resourceUri, resourceUri, { mimeType: RESOURCE_MIME_TYPE }, async () => ({
    contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: await fs.readFile(htmlPath, "utf-8") }],
  }));
}
