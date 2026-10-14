"""Shared extract readers and plan geometry for the analysis scripts (standard library only).

Units: feet for coordinates (as revit-mcp returns them), m² for areas.
"""
import csv
import glob
import json
import math
import os

FT = 0.3048
SQFT = FT * FT


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_parts(raw, pattern):
    rows = []
    for p in sorted(glob.glob(os.path.join(raw, pattern))):
        rows += read_tsv(p)
    return rows


def schedule_rows(path):
    """All rows of a Revit schedule export.  Comma or tab delimited (revit-mcp writes commas, mcp-servers-for-revit
    tabs): the delimiter is taken from the header line."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = [l for l in text.splitlines() if l.strip()]
    probe = lines[1] if len(lines) > 1 else (lines[0] if lines else "")
    delim = "\t" if probe.count("\t") > probe.count(",") else ","
    return list(csv.reader(text.splitlines(), delimiter=delim))


def read_schedule_csv(path):
    """Revit schedule CSV export -> (title, header, data rows). Blank rows are kept out; group/total rows are kept."""
    rows = schedule_rows(path)
    title = rows[0][0] if rows and rows[0] else ""
    header = rows[1] if len(rows) > 1 else []
    data = [r for r in rows[2:] if any(c.strip() for c in r)]
    return title, header, data


def point_in_poly(x, y, loop):
    inside = False
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


class Room:
    def __init__(self, r, polys, rect_ratio=1.04):
        self.id = int(r["id"])
        self.name = r["name"]
        self.number = r["number"]
        self.level = r["level"]
        self.area = float(r["area_m2"])
        self.bb = [float(r[k]) for k in ("minx", "miny", "minz", "maxx", "maxy", "maxz")]
        self.poly = polys.get(str(self.id))
        bbox_area = (self.bb[3] - self.bb[0]) * (self.bb[4] - self.bb[1]) * SQFT
        self.rect = self.area > 0 and bbox_area / self.area <= rect_ratio
        self.shape = "polygon" if self.poly else ("bbox (rectangular)" if self.rect else "bbox (non-rectangular)")

    @property
    def label(self):
        return "%s %s" % (self.name, self.number)

    def contains_xy(self, x, y):
        b = self.bb
        if not (b[0] <= x <= b[3] and b[1] <= y <= b[4]):
            return False
        if self.poly:
            return point_in_poly(x, y, self.poly[0]) and not any(point_in_poly(x, y, h) for h in self.poly[1:])
        return True

    def contains(self, x, y, z):
        return self.bb[2] - 0.05 <= z < self.bb[5] and self.contains_xy(x, y)


def load_rooms(raw):
    polys = {}
    p = os.path.join(raw, "room_polygons.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            polys = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    return [Room(r, polys) for r in read_tsv(os.path.join(raw, "rooms.tsv"))]


def room_at(rooms, x, y, z):
    hits = [r for r in rooms if r.area > 0 and r.contains(x, y, z)]
    if not hits:
        return None
    return min(hits, key=lambda r: r.area)          # most specific room when bboxes overlap


def rooms_touching_box(rooms, bb, z, grow=1.0, n=7):
    """Rooms that a grid of points over an (enlarged) plan box falls in, at height z. Returns {room: hits}."""
    x0, y0, x1, y1 = bb[0] - grow, bb[1] - grow, bb[3] + grow, bb[4] + grow
    out = {}
    for i in range(n):
        for j in range(n):
            x = x0 + (x1 - x0) * i / (n - 1)
            y = y0 + (y1 - y0) * j / (n - 1)
            r = room_at(rooms, x, y, z)
            if r is not None:
                out[r] = out.get(r, 0) + 1
    return out


def ceil_div(a, b):
    return int(math.ceil(a / b - 1e-9))
