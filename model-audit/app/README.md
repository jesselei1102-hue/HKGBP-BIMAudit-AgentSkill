# Ultraviolet MCP App template

A runnable MCP App starter in the Ultraviolet theme (minimalist · abstract · future; light and dark):
a stdio MCP server with one UI tool, plus a single-file vanilla-TypeScript UI.

```
src/            server — index.ts (stdio), app.ts (tools + ui:// resource), data.ts (example data)
app/            UI — app.html (shell), main.ts (example app)
  theme/        tokens.css (colours), components.css (all component styles), theme.ts (light/dark + toggle),
                glyphs.ts (line glyphs for 40 Revit categories — categoryGlyph(name))
  ui/           tabs.ts, popover.ts, context.ts (share state with the model), html.ts (escape, pad3, glyph, plural)
dev/harness.html  mock MCP host for testing in a browser
test/           vitest unit tests
```

## Run and build

```bash
npm install
npm test            # unit tests
npm run build       # tsc (server → build/) + vite (UI → build/app/app.html)
npm start           # runs the stdio server (normally your MCP host starts it)
```

## Make it your app

1. Rename: `name` in `package.json` and `APP_NAME` in `src/app.ts` (used for the server name and the `ui://` address).
2. Replace `src/data.ts` with your data access, and the two tools in `src/app.ts` with yours.
   Keep the UI tool's `_meta: { ui: { resourceUri } }`; tools the UI calls (like `update_item`) don't need a UI.
3. Rewrite `app/main.ts` for your data. Keep `initTheme`, `applyInitialHostTheme`, `initTabs`, `initPopovers`
   and `createModelContext`, and use only classes from `components.css`.
4. `npm test && npm run build`, then check it in the harness (below) in both themes.

## Register with a host

The UI address contains a hash of `build/app/app.html` (`ui://<APP_NAME>/app-<hash>.html`), so a rebuilt UI is
never confused with a cached one. **After every rebuild, reconnect or restart the server** — hosts read the tool
list (and with it the address) only when they connect. In Claude desktop, a window close is not a restart: quit
from the system tray.

**Claude desktop** (chat and the Code tab both use these servers): add an entry under `mcpServers` in
`claude_desktop_config.json` — on this machine
`C:\Users\Datech\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\claude_desktop_config.json`
(standard installs: `%APPDATA%\Claude\claude_desktop_config.json`; or Settings → Developer → Edit config).
Then quit Claude from the system tray and reopen it.

```json
{
  "mcpServers": {
    "ultraviolet-example": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": ["C:\\path\\to\\your-app\\build\\index.js"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` in the project, or `~/.cursor/mcp.json`): same shape, plus `"type": "stdio"`.

**Claude Code CLI** (`~/.claude.json` → `mcpServers`, or a project `.mcp.json`): same shape as Cursor.

## Test in a browser without a host

```bash
python -m http.server 8790      # from this folder
```

Open `http://localhost:8790/dev/harness.html?theme=dark` (or `light`). The harness answers `ui/initialize`,
simulates `show_items` / `update_item` in the page (same rules as `src/data.ts` — keep them in sync), records
model-context updates, and has buttons to switch the host theme. For scripted checks it exposes
`window.calls`, `window.lastContext` and `window.items`.

## Keeping apps in sync with the theme

Apps copy the template, so a theme change does not propagate. To bring an existing app up to date, compare its
copies of `app/theme/tokens.css` and `app/theme/components.css` with this folder's. The Revit Schedule app
(`Cursor Projects\Revit MCP\src\mcp-servers-for-revit\server\mcp-app\app.html`) keeps the same tokens and class
names inline in its `<style>`.
