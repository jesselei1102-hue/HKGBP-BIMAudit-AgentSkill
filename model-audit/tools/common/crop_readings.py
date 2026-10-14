#!/usr/bin/env python3
"""Cut the table cell behind each sheet reading out of its sheet export, so the reading can be checked.  Needs Pillow.

Usage: python crop_readings.py --raw <extract dir> [--file table_values.tsv]
Reads <raw>/<file>; for every row with a `box` ("x0,y0,x1,y1", pixels of the sheet export in <raw>/sheets/), saves
<raw>/crops/<key>.png (enlarged 2x) and writes its path into the `crop` column.  Rows without a box keep their crop.
A reading with a crop is verified: only verified readings can make a table check FAIL (tools/common/readings.py).
"""
import argparse, glob, os
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--file", default="table_values.tsv")
    a = ap.parse_args()
    path = os.path.join(a.raw, a.file)
    with open(path, encoding="utf-8-sig") as f:
        lines = [l.rstrip("\r\n").split("\t") for l in f if l.strip()]
    head, rows = lines[0], lines[1:]
    if "crop" not in head:
        head.append("crop")
    rows = [r + [""] * (len(head) - len(r)) for r in rows]
    ix = {h: i for i, h in enumerate(head)}
    if "box" not in ix:
        print("no `box` column: nothing to crop")
        return 0
    os.makedirs(os.path.join(a.raw, "crops"), exist_ok=True)
    n, missing = 0, []
    for r in rows:
        box = r[ix["box"]].strip()
        if not box:
            continue
        hits = glob.glob(os.path.join(a.raw, "sheets", "*Sheet - %s *.png" % r[ix["sheet"]]))
        if not hits:
            missing.append(r[ix["key"]])
            continue
        x0, y0, x1, y1 = (int(float(v)) for v in box.split(","))
        im = Image.open(hits[0]).convert("RGB").crop((x0, y0, x1, y1))
        im = im.resize((im.width * 2, im.height * 2))
        rel = "crops/%s.png" % r[ix["key"]]
        im.save(os.path.join(a.raw, rel))
        r[ix["crop"]] = rel
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join("\t".join(r) for r in [head] + rows) + "\n")
    print("cropped %d readings" % n + ("; sheet export not found for: " + ", ".join(missing) if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
