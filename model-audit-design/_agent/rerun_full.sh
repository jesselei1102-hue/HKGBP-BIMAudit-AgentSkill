#!/usr/bin/env bash
# Re-run G3 -> G5 analyses, group reports, the combined audit-results.json and both reports from the saved extracts.
# G1 (S14) and G2 are re-run too; their extracts did not change.  Read-only on the model (no MCP calls).
set -e
W="$(cd "$(dirname "$0")/../.." && pwd)"
T="$W/model-audit/tools"
R="$W/model-audit-runs"
N=GBP_Revit_Templates_R27-GBPSkills
M="$N.rvt"
PY="python -I"
S14="$R/audit-2026-10-13-s14/C14_analysis_$N.json"
G2="$R/audit-2026-10-13-g2/G2_analysis_$N.json"
G3="$R/audit-2026-10-13-g3/G3_analysis_$N.json"
G4="$R/audit-2026-10-13-g4/G4_analysis_$N.json"
G5="$R/audit-2026-10-13-g5/G5_analysis_$N.json"

$PY "$T/s14_lv/analyze.py" --raw "$R/audit-2026-10-13-s14/_raw" --project "$N" --model "$M" --out "$S14" \
    --schedule "$(ls "$R"/audit-2026-10-13-s14/_raw/*S14*.csv | head -1)" --fixtures "$R/audit-2026-10-13-g2/_raw/fixtures.tsv" > "$R/audit-2026-10-13-s14/analysis_console.txt"
$PY "$T/s14_lv/report.py" --analysis "$S14" --outdir "$R/audit-2026-10-13-s14" --date 20261013 > /dev/null
$PY "$T/room_use/analyze.py" --raw "$R/audit-2026-10-13-g2/_raw" --project "$N" --model "$M" --out "$G2" > "$R/audit-2026-10-13-g2/analysis_console.txt"
$PY "$T/common/task_report.py" --analysis "$G2" --outdir "$R/audit-2026-10-13-g2" --name RoomUse --date 20261013 > /dev/null
$PY "$T/area_scheme/analyze.py" --raw "$R/audit-2026-10-13-g3/_raw" --project "$N" --model "$M" --out "$G3" --g2 "$G2" > "$R/audit-2026-10-13-g3/analysis_console.txt"
$PY "$T/common/task_report.py" --analysis "$G3" --outdir "$R/audit-2026-10-13-g3" --name AreaScheme --date 20261013 > /dev/null
$PY "$T/drawings/analyze.py" --raw "$R/audit-2026-10-13-g4/_raw" --project "$N" --model "$M" --out "$G4" --s14 "$S14" --g3 "$G3" > "$R/audit-2026-10-13-g4/_raw/analysis_console.txt"
$PY "$T/common/task_report.py" --analysis "$G4" --outdir "$R/audit-2026-10-13-g4" --name Drawings --date 20261013 > /dev/null
$PY "$T/lists_health/analyze.py" --raw "$R/audit-2026-10-13-g5/_raw" --project "$N" --model "$M" --out "$G5" \
    --g2 "$G2" --g3 "$G3" --g4 "$G4" --s14 "$S14" --g3raw "$R/audit-2026-10-13-g3/_raw" --g4raw "$R/audit-2026-10-13-g4/_raw" \
    --schedules "$R/audit-2026-10-13-g5/_raw/all_schedules.tsv" > "$R/audit-2026-10-13-g5/analysis_console.txt"
$PY "$T/common/task_report.py" --analysis "$G5" --outdir "$R/audit-2026-10-13-g5" --name ListsHealth --date 20261013 > /dev/null

F="$R/audit-2026-10-13-full"
$PY "$T/common/build_results.py" --out "$F/audit-results.json" --project "BD Sample - Proposed Institutional Development at Kowloon" \
    --model "$M" --date 2026-10-13 --s14 "$R/audit-2026-10-13-s14/audit-results.json" \
    --decisions "$F/decisions.json" --harness "Claude Code" \
    --group "$G2" "$R/audit-2026-10-13-g2" --group "$G3" "$R/audit-2026-10-13-g3" \
    --group "$G4" "$R/audit-2026-10-13-g4" --group "$G5" "$R/audit-2026-10-13-g5" \
    --crop "$R/audit-2026-10-13-g3/_raw/crop_c003_summary.png" AUD-S08 "C003 GFA concession summary (picture table)" \
    --crop "$R/audit-2026-10-13-g4/_raw/crop_a001_block.png" AUD-V01 "A001 block plan: site fill and coordinates table" \
    --crop "$R/audit-2026-10-13-g4/_raw/crop_a007_levels.png" AUD-V04 "A007 level heads read 'SFL … m'" \
    --crop "$R/audit-2026-10-13-g3/_raw/crop_c005_c006.png" AUD-S12 "C005 / C006 calculation lines" \
    --crop "$R/audit-2026-10-13-g3/_raw/crops/height_c001.png" AUD-S05 "C001 building height 12.15 m" \
    --crop "$R/audit-2026-10-13-g3/_raw/crops/height_devsched.png" AUD-S05 "Development Schedule height 17.35 m"
$PY "$W/model-audit/report/render_report.py" --results "$F/audit-results.json" --audience bim --out "$F/report-bim.html"
$PY "$W/model-audit/report/render_report.py" --results "$F/audit-results.json" --audience ap --out "$F/report-ap.html"
