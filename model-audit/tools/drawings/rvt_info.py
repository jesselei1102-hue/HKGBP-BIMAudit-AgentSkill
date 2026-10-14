#!/usr/bin/env python3
"""Read the BasicFileInfo text that Revit writes into every .rvt (UTF-16): format year, build, worksharing.

Usage: python rvt_info.py <model.rvt> --out rvt_info.json      Read-only; stdlib only.
Closes GAP-04 when the harness can read the model file on disk.
"""
import argparse, json, os, re

ap = argparse.ArgumentParser()
ap.add_argument("rvt")
ap.add_argument("--out", required=True)
a = ap.parse_args()
with open(a.rvt, "rb") as f:
    data = f.read()
info = {"file": os.path.basename(a.rvt), "size_bytes": len(data), "size_mb": round(len(data) / 1048576, 2)}
for key in ("Format", "Build", "Worksharing"):
    s = (key + ": ").encode("utf-16-le")
    i = data.find(s)
    if i >= 0:
        txt = data[i + len(s): i + len(s) + 120].decode("utf-16-le", "replace")
        info[key.lower()] = re.split(r"[\r\n\x00]", txt)[0].strip()
folder = os.path.dirname(os.path.abspath(a.rvt))
info["other_rvt_in_folder"] = sorted(f for f in os.listdir(folder) if f.lower().endswith(".rvt") and f != info["file"])
with open(a.out, "w", encoding="utf-8") as f:
    json.dump(info, f, indent=1)
print(info)
