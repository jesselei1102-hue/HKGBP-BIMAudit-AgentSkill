# gbp-audit · chat window for the GBP Model Audit

A small MCP server that shows one window inside the chat (an MCP App). The window only chooses; the reports carry the
results.

- **Run sheet** (top): what this run will do: the checks (n of 37 and their sections), the outputs, and where the
  results go (a new audit folder, or *Add to an earlier audit instead*). It holds the one *Run n checks* button;
  when nothing can run yet it says why.
- **Checks**: the BIMGBPS sections (Views, Schedules, Assembly and export, Model health) with selected / total,
  plus *Full audit* and *Clear*; the section's tasks (name, `TL-xx · §clause`) with search and *Select all*. On
  narrow windows the section list becomes a row of tabs.
- **Outputs**: BIM team report (`report-bim.html`), AP / client report (`report-ap.html`), Excel issue list
  (`issues.xlsx`). All three are ticked by default; at least one is needed.

*Run* sends the instruction to the chat (the agent follows `../RUN.md` with the Revit MCP tools it finds, builds the
chosen outputs straight away, and says where they are), and the window then shows what happens next. If the host
refuses the message, the window shows the instruction to paste. There is no review window and no confirmation gate:
values read off sheet images are listed in the reports as not checked by a person, with their crops.

The server does not talk to Revit and does not use the network. It only reads the package and lists the runs
folder. Without it the audit still runs from the text prompts in `../RUN.md` §7.

## Build

Needs Node.js 20 or later.

```bash
npm install
npm run build
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
| `choose_checks` | agent | Opens the window (task list from `../tasks.json`, earlier audits in the runs folder) |

## Develop

The tests (`test/`, `npm test`) and the browser harness (`dev/harness.html`) are kept locally by the
maintainer and are not published in this repository.

`../tasks.json` is generated: after changing an analyser's `GROUP` list or an L2 card title, run
`python ../tools/common/make_tasks_json.py`.
