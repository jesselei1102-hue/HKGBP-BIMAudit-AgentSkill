#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { APP_NAME, registerApp } from "./app.js";
import { resolveConfig } from "./config.js";

const server = new McpServer({ name: APP_NAME, version: "0.1.0" });

async function main() {
  const config = resolveConfig(process.argv.slice(2), process.env, path.dirname(fileURLToPath(import.meta.url)));
  await registerApp(server, config);
  await server.connect(new StdioServerTransport());
  console.error(`${APP_NAME} MCP server started (runs: ${config.runsRoot})`);
}

main().catch((error) => {
  console.error(`Error starting ${APP_NAME}:`, error);
  process.exit(1);
});
