# Changelog

All notable changes to the GBP Model Audit package. Versions follow [Semantic Versioning](https://semver.org/);
0.x releases are pre-releases.

## [0.1.0] - 2026-10-27

First pre-release.

### Added

- Model Audit package for Revit models prepared for a Hong Kong GBP Stage I submission: four layers (L1 domain,
  L2 task logic, L3 Revit SOP, L4 MCP capabilities) covering the 36 BIMGBPS tasks (TL-S01–S18, TL-V01–V14,
  TL-A01–A04) and model health MA-1 to MA-7.
- Five executable tool groups (`tools/s14_lv`, `room_use`, `area_scheme`, `drawings`, `lists_health`) with MCP
  response extractors (`tools/extract/g1`–`g5`), two-stage runs (analysis, then report) and an English report in two
  editions (BIM team, AP / client), as Excel and HTML.
- Run modes: full audit, group by group, single task (`--tasks` / `--update`) and regression against an earlier
  `audit-results.json`.
- Six Agent Skills (`skills/`) that the audit agent installs and updates itself (RUN.md §1 step 0).
- Capability bindings for two Revit MCP servers: revit-mcp and mcp-servers-for-revit, plus an onboarding guide for
  connecting any other MCP (`L4-Capabilities/CAP-onboarding.md`).
- Plain-language README for APs and a task-to-legislation table.
- Optional chat window (`model-audit/app/`, an MCP App, server `gbp-audit`): a guided Choose checks window (tasks by
  BIMGBPS section, earlier audits) and a guided Review window (steps bar, checks grouped by task and item, crop
  images for each reading).
- Reading review gate: readings are marked against the values reviewed, the window records which review lists were
  looked at, and a tick carries over only while its list is unchanged; the reports show the review state.

### Fixed

- Tab-separated schedule CSVs, G5 parking counts, and G4 unread readings counted as read (found in the 2026-10-14
  to 15 full runs).
- Reports for a new audit of only a few tasks; gate for merged audits.
- Overview window: open and copy actions, posting to the chat, stale review ticks, Run sent twice.

### Changed

- Tests, validation scripts, fixtures and the window's dev harness are kept by the maintainer and are not published
  in this repository.

[0.1.0]: https://github.com/jesselei1102-hue/HKGBP-BIMAudit-AgentSkill/releases/tag/v0.1.0
