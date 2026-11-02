#!/usr/bin/env python3
"""Screenshots of what failed, for the fix list.  One shot per Revit object, however many rows point at it.

  python shots.py plan   --results <run>/audit-results.json [--views views_on_sheets.tsv]
  (the agent captures each row of <run>/_raw/shots/plan.tsv through the MCP, see RUN.md 6e)
  python shots.py attach --results <run>/audit-results.json

plan: lists every object with action "fix" once: view / sheet rows are exported whole (mode view); rooms and other
elements are zoomed to in the floor plan of their level (mode zoom), found by the floor in the room's level name
("SFL 8.75_2/F" -> a plan view named "... 2/F").  A row with no view_id says why in `note` and gets no shot.
attach: takes the PNG in _raw/shots/<element_id>/, fits it in 1600 px, writes assets/shot-NNN.png and a thumbnail
(Pillow; without Pillow the export is copied and is its own thumbnail) and sets issue.shot.  A room in mode zoom gets a
red frame on its plan bounding box from <run>/_raw/rooms*.tsv; other objects get none.  File names carry no Revit
ID, because the AP edition must not show one.  Run it after build_results.py, which rewrites the results.
"""
import argparse, csv, glob, json, os, re, shutil

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

LIMIT, THUMB = 1600, (192, 144)
FRAME, FRAME_W, ZOOM_FILL = (225, 0, 0), 5, 0.5
COLS = ["element_id", "kind", "object", "mode", "view_id", "view_name", "note"]
FLOOR = re.compile(r"_([^_\s,)]+/F)\b")


def read_views(path):
    if not path:
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r.get("view_type") == "FloorPlan"]


def host_view(obj, views):
    """The floor plan on a sheet for this object's floor; (None, why) when it cannot be told."""
    m = FLOOR.search(obj)
    if not m:
        return None, "no floor in the object name"
    hits = [v for v in views if v["view_name"].endswith(" " + m.group(1))]
    return (hits[0], "") if hits else (None, "no floor plan on a sheet for " + m.group(1))


def plan(a, run, results):
    views = read_views(a.views)
    rows = {}
    for i in results.get("issues", []):
        oid = i.get("element_id")
        if i["action"] != "fix" or not oid or oid in rows:
            continue
        row = {"element_id": oid, "kind": i.get("kind") or "", "object": i["object"], "mode": "zoom",
               "view_id": "", "view_name": "", "note": ""}
        if i.get("kind") in ("view", "sheet"):
            row.update(mode="view", view_id=oid, view_name=i["object"])
        else:
            v, row["note"] = host_view(i["object"], views)
            if v:
                row.update(view_id=v["view_id"], view_name=v["view_name"])
        rows[oid] = row
    out = os.path.join(run, "_raw", "shots")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "plan.tsv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLS, delimiter="\t")
        w.writeheader()
        w.writerows(rows.values())
    no = [r for r in rows.values() if not r["view_id"]]
    print("wrote %s: %d objects to capture, %d with no view" % (path, len(rows) - len(no), len(no)))
    for r in no:
        print("  no view: %s (%s): %s" % (r["object"], r["element_id"], r["note"]))
    return 0


def read_boxes(run):
    """Plan bounding boxes in feet from the rooms extract: {room id: (width, height)}."""
    boxes = {}
    for path in glob.glob(os.path.join(run, "_raw", "rooms*.tsv")):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                try:
                    boxes[r["id"]] = (float(r["maxx"]) - float(r["minx"]), float(r["maxy"]) - float(r["miny"]))
                except (KeyError, TypeError, ValueError):
                    pass
    return boxes


def frame_of(size, box):
    """zoom_to_elements centres the object and fits it in half the window (measured on Revit 2027, RUN.md 6e)."""
    w, h = size
    k = ZOOM_FILL * min(w / box[0], h / box[1])
    bw, bh = box[0] * k, box[1] * k
    return (w - bw) / 2, (h - bh) / 2, (w + bw) / 2, (h + bh) / 2


def thumb_around(im, frame):
    """The thumbnail shape around the frame with some of the drawing outside it; centred when there is no frame."""
    w, h = im.size
    if not frame:
        cw, ch = (w, w * THUMB[1] / THUMB[0]) if w / h < THUMB[0] / THUMB[1] else (h * THUMB[0] / THUMB[1], h)
    else:
        cw = min(w, max((frame[2] - frame[0]) * 1.25, (frame[3] - frame[1]) * 1.25 * THUMB[0] / THUMB[1]))
        ch = min(h, cw * THUMB[1] / THUMB[0])
    x0, y0 = int((w - cw) / 2), int((h - ch) / 2)
    out = im.crop((x0, y0, int((w + cw) / 2), int((h + ch) / 2))).resize(THUMB, Image.LANCZOS)
    if frame:                       # drawn at thumbnail size, or the line would thin away with the scaling
        k = THUMB[0] / cw
        ImageDraw.Draw(out).rectangle([(frame[0] - x0) * k, (frame[1] - y0) * k, (frame[2] - x0) * k, (frame[3] - y0) * k],
                                      outline=FRAME, width=3)
    return out


def save(src, assets, name, box=None):
    """Fit the export, draw the object's frame and write the thumbnail.  Returns png, thumb, framed."""
    png, thumb = name + ".png", name + "-t.png"
    if Image is None:
        shutil.copyfile(src, os.path.join(assets, png))
        return png, png, False
    im = Image.open(src).convert("RGB")
    im.thumbnail((LIMIT, LIMIT))
    frame = frame_of(im.size, box) if box and box[0] > 0 and box[1] > 0 else None
    thumb_around(im, frame).save(os.path.join(assets, thumb), optimize=True)
    if frame:
        ImageDraw.Draw(im).rectangle(frame, outline=FRAME, width=FRAME_W)
    im.quantize(128).save(os.path.join(assets, png), optimize=True)
    return png, thumb, bool(frame)


def attach(a, run, results):
    path = os.path.join(run, "_raw", "shots", "plan.tsv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assets = os.path.join(run, "assets")
    os.makedirs(assets, exist_ok=True)
    for old in glob.glob(os.path.join(assets, "shot-*.png")):
        os.remove(old)
    shots, missing, boxes = {}, [], read_boxes(run)
    for n, r in enumerate(rows, 1):
        hits = sorted(glob.glob(os.path.join(run, "_raw", "shots", r["element_id"], "*.png")), key=os.path.getmtime)
        if not hits:
            if r["view_id"]:
                missing.append(r["object"])
            continue
        box = boxes.get(r["element_id"]) if r["mode"] == "zoom" else None
        png, thumb, framed = save(hits[-1], assets, "shot-%03d" % n, box)
        shots[r["element_id"]] = {"file": png, "thumb": thumb, "view": re.sub(r"\s*\([A-Z][A-Za-z]+\)$", "", r["view_name"]),
                                  "mode": r["mode"], "framed": framed}
    linked = 0
    for i in results.get("issues", []):
        i.pop("shot", None)
        if i["action"] == "fix" and i.get("element_id") in shots:
            i["shot"] = shots[i["element_id"]]
            linked += 1
    with open(a.results, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("attached %d screenshots to %d rows" % (len(shots), linked)
          + ("; not captured: " + ", ".join(missing) if missing else ""))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["plan", "attach"])
    ap.add_argument("--results", required=True)
    ap.add_argument("--views")
    a = ap.parse_args()
    with open(a.results, encoding="utf-8-sig") as f:
        results = json.load(f)
    return (plan if a.step == "plan" else attach)(a, os.path.dirname(os.path.abspath(a.results)), results)


if __name__ == "__main__":
    raise SystemExit(main())
