"""Kept for old instructions: use tools/extract/g3_extract.py.

Usage: python parse_areas.py <extract dir>   ==   python ../extract/g3_extract.py --mcp <extract dir>/mcp --out <extract dir>
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else "."
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "extract", "g3_extract.py")
    sys.exit(subprocess.call([sys.executable, script, "--mcp", os.path.join(raw, "mcp"), "--out", raw] + sys.argv[2:]))
