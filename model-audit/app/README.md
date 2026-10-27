# gbp-audit · chat window for the GBP Model Audit

A small MCP server that shows two windows inside the chat (an MCP App):

1. **Choose checks** – the operator ticks tasks (grouped G1–G5), chooses a new audit or an existing one, and the
   window sends the matching instruction to the chat. The agent then runs the audit as `../RUN.md` says, using the
   Revit MCP that is connected.
2. **Overview** – after the analysis the agent opens this window: counts per task, every FAIL / UNCLEAR check
   ("Check this yourself"), the sheet readings with their crops to mark *Correct* or *Wrong*, and missing inputs.
   This is the confirmation gate: *Confirm and build reports*, *Send back for re-reading*, or *Build reports without
   full review*. The review is saved as `gate-confirmation.json` in the run folder and the reports list any reading
   nobody checked. After the reports are built the same window lists them.

The server does not talk to Revit and does not use the network. It reads and writes only the package and the runs
folder. Without it the audit still runs from the text prompts in `../RUN.md` §7.

## Build

Needs Node.js 20 or later.

```bash
npm install
npm run build
npm test
```

## Register

`args` is the absolute path to `build/index.js`. Add `"--runs", "<folder>"` to use a runs folder other than
`model-audit-runs` next to the package (or set `GBP_AUDIT_RUNS`).

**Claude Code** (project `.mcp.json`, or `~/.claude.json` → `mcpServers`):

```json
{
  "mcpServers": {
    "gbp-audit": {
      "type": "stdio",
      "command": "node",
      "args": ["C:\\path\\to\\model-audit\\app\\build\\index.js"]
    }
  }
}
```

**Claude desktop**: the same entry without `"type"` in `claude_desktop_config.json`, then quit Claude from the system
tray and reopen it.

**Cursor**: the same entry as Claude Code in `.cursor/mcp.json` or `~/.cursor/mcp.json`.

Keep the Revit MCP registered as well; the agent uses it to read the model.

After every rebuild, reconnect or restart the server: hosts read the tool list (and with it the window address) only
when they connect.

## Tools

| Tool | Called by | Does |
| --- | --- | --- |
| `choose_checks` | agent | Opens the Choose checks window (task list from `../tasks.json`, earlier audits in the runs folder) |
| `show_overview(run)` | agent | Opens the Overview window for one run folder |
| `get_crop(run, file)` | window only | One crop image as base64 (png / jpg, at most 5 MB, inside the run folder) |
| `save_gate(run, marks, mode)` | window only | Writes `<run>/gate-confirmation.json` (`confirmed` needs every reading marked correct) |

## Develop

```bash
npm run build && npm run fixture:overview
python -m http.server 8790      # from the model-audit folder
```

Open `http://localhost:8790/app/dev/harness.html` (parameters: `theme=dark`, `view=overview`, `reports=0`, `error=1`,
`nomessage=1`, `gatefail=1`, `xss=1`). The harness simulates the four tools and records `window.calls`,
`window.messages` and `window.lastContext`.

`../tasks.json` is generated: after changing an analyser's `GROUP` list or an L2 card title, run
`python ../tools/common/make_tasks_json.py`.
