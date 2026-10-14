#!/usr/bin/env python3
"""Pixel sampling on exported sheet PNGs (AGENT-IMAGE-SAMPLE).  Needs Pillow.

Usage: python sample_colours.py --sheets <dir with Export_* PNGs> --out colour_samples.json [--regions regions.json]
regions.json: {"<label>": {"sheet": "C002", "box": [x0, y0, x1, y1]}, ...}   (pixels of the 1920 px export)
For each region: pixel counts of the six BIMGBPS Table 1 colours, the site pink, the share of grey (halftone) and
black pixels, and the 8 most common colours.
Always also: one entry per exported sheet, "sheet_<number>", over the drawing area (border and the title-block strip
on the right left out), with the same counts plus, per Table 1 class, the largest count of a single near-miss colour
(within RGB distance 40 but not exact).  No region boxes are needed for those.  Read-only.
"""
import argparse, collections, glob, json, os, re
from PIL import Image

TABLE1 = {"1": (255, 164, 25), "2": (227, 100, 102), "3a": (191, 0, 255), "3b": (222, 184, 135), "4a": (30, 144, 255),
          "4b": (144, 214, 236)}
PINK = (255, 218, 236)


def pixels(im):
    return getattr(im, "get_flattened_data", im.getdata)()


def stats(c):
    tot = sum(c.values())
    grey = sum(v for (x, y, z), v in c.items() if x == y == z and 60 < x < 235)
    black = sum(v for (x, y, z), v in c.items() if x < 40 and y < 40 and z < 40)
    return {"pixels": tot, "table1": {k: c.get(v, 0) for k, v in TABLE1.items()}, "pink": c.get(PINK, 0),
            "grey_pct": round(100.0 * grey / tot, 2) if tot else 0, "black_pct": round(100.0 * black / tot, 2) if tot else 0,
            "top": [[list(k), v] for k, v in c.most_common(8)]}


def near_miss(c):
    out = {}
    for k, ref in TABLE1.items():
        n = [v for rgb, v in c.items() if rgb != ref and sum((a - b) ** 2 for a, b in zip(rgb, ref)) <= 1600]
        out[k] = max(n) if n else 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions")
    ap.add_argument("--sheets", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    regions = {}
    if a.regions and os.path.exists(a.regions):
        with open(a.regions, encoding="utf-8") as f:
            regions = json.load(f)
    out, cache = {}, {}

    def sheet(code):
        if code not in cache:
            hits = glob.glob(os.path.join(a.sheets, "*Sheet - %s *.png" % code))
            cache[code] = Image.open(hits[0]).convert("RGB") if hits else None
        return cache[code]

    for label, r in regions.items():
        im = sheet(r["sheet"])
        if im is None:
            out[label] = {"sheet": r["sheet"], "error": "sheet export not found"}
            continue
        out[label] = dict({"sheet": r["sheet"], "box": r["box"]},
                          **stats(collections.Counter(pixels(im.crop(tuple(r["box"]))))))
    for p in sorted(glob.glob(os.path.join(a.sheets, "*Sheet - *.png"))):
        m = re.search(r"Sheet - (\S+) ", os.path.basename(p))
        if not m:
            continue
        im = sheet(m.group(1))
        w, h = im.size
        box = [int(0.02 * w), int(0.03 * h), int(0.90 * w), int(0.97 * h)]
        c = collections.Counter(pixels(im.crop(tuple(box))))
        e = dict({"sheet": m.group(1), "box": box, "mode": "whole sheet"}, **stats(c))
        nonwhite = sum(v for k, v in c.items() if min(k) < 245)
        e["nonwhite"] = nonwhite
        e["near_table1"] = near_miss(c)
        out["sheet_" + m.group(1)] = e
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("sampled %d regions, %d sheets" % (len(regions), sum(1 for k in out if k.startswith("sheet_"))))


if __name__ == "__main__":
    main()
