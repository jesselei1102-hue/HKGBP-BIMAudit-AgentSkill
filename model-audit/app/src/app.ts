import { registerAppResource, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Config } from "./config.js";

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

export async function registerApp(server: McpServer, config: Config): Promise<void> {
  void config;
  const htmlPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "app", "app.html");
  const resourceUri = await versionedResourceUri(APP_NAME, htmlPath);

  registerAppResource(server, resourceUri, resourceUri, { mimeType: RESOURCE_MIME_TYPE }, async () => ({
    contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: await fs.readFile(htmlPath, "utf-8") }],
  }));
}
