# gbp-audit · chat window for the GBP Model Audit

A small MCP server that shows two windows inside the chat (an MCP App).

Both windows show the four steps at the top (1 Choose › 2 Analyse › 3 Review › 4 Reports), a list on the left and
the selected list on the right (on narrow windows the left list becomes a row of tabs).

1. **Choose checks** – the left list holds the BIMGBPS sections (Views, Schedules, Assembly and export, Model
   health) with selected / total, plus *Full audit* and *Clear*. The right side lists the section's tasks
   (name, `TL-xx · §clause`) with search and *Select all*; the line underneath names the new audit, or picks an
   earlier one with *Add to an earlier audit instead*. *Run n checks* sends the matching instruction to the chat
   and the window then says what happens next (the agent runs the audit as `../RUN.md` says, using the Revit MCP
   tools it finds; a review window follows; then the reports). If the host refuses the message, the window shows
   the instruction to paste.
2. **Overview** – after the analysis the agent opens this window. It is the confirmation gate, laid out as a
   to-do list: *Failures*, *Check yourself* (UNCLEAR), *Missing inputs* (`-INPUT` checks and data warnings),
   *Sheet readings*, and *All checks* (the per-task table). Checks with the same task and item show as one card
   (first 4 objects, `+n more`, then `Fix:` or `Look at:`; click for the details). The first three lists are
   ticked with *I've seen these* / *I've checked these*; the readings are done when each one is marked
   *Correct* (marked ones fold away). *Build reports* opens once all four are done; *Send back for re-reading*
   replaces it while a reading is marked *Wrong*; *Build without full review* is always there. The review is
   saved as `gate-confirmation.json` (with `reviewed`: which lists were looked at) and the reports name any
   reading nobody checked and any list not looked at. After the reports are built the same window opens on
   *Reports* (step 4).

The server does not talk to Revit and does not use the network. It reads and writes only the package and the runs
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
| `choose_checks` | agent | Opens the Choose checks window (task list from `../tasks.json`, earlier audits in the runs folder) |
| `show_overview(run)` | agent | Opens the Overview window for one run folder |
| `get_crop(run, file)` | window only | One crop image as base64 (png / jpg, at most 5 MB, inside the run folder) |
| `save_gate(run, marks, mode, reviewed?, reviewed_counts?)` | window only | Writes `<run>/gate-confirmation.json` (`confirmed` needs every reading marked correct; `reviewed` records which lists were looked at, `reviewed_counts` how long each was, so a tick only carries over while its list is unchanged) |

## Develop

The tests (`test/`, `npm test`) and the browser harness (`dev/`, `npm run fixture:overview`) are kept locally by the
maintainer and are not published in this repository.

`../tasks.json` is generated: after changing an analyser's `GROUP` list or an L2 card title, run
`python ../tools/common/make_tasks_json.py`.
