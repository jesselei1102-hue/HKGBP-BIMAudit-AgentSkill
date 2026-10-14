"""Values read off exported sheet images (table_values.tsv, readings.tsv): load them and keep the provenance rules.

A reading is what a person or agent saw on the sheet. Rules (AUD-000 §10, G3 §3):
  - A row whose note says the value came from the model (MODEL, FILLED, model extract, assume …) is not a reading:
    it is dropped and reported, so a table check never compares the model with itself.
  - A row without a value, or with confidence other than high / medium, is not a reading.
  - `crop` (optional column): path, relative to the extract folder, of an image of the table cell. A reading with an
    existing crop is verified. A mismatch with the model is FAIL only for verified readings; otherwise UNCLEAR.
Stdlib only.
"""
import os
import re

from geom import read_tsv

NOT_A_READING = re.compile(r"\bMODEL\b|FILLED|model extract|from (the )?model|\bassum", re.I)


def load(path, raw_dir):
    """Return (readings by key, list of (key, reason) rejected)."""
    rows = read_tsv(path) if os.path.exists(path) else []
    good, rejected = {}, []
    for r in rows:
        why = None
        if not (r.get("value") or "").strip():
            why = "no value"
        elif NOT_A_READING.search(r.get("note") or ""):
            why = "model value or assumption, not read from the sheet"
        elif (r.get("confidence") or "").lower() not in ("high", "medium"):
            why = "confidence %r" % (r.get("confidence") or "")
        if why:
            rejected.append((r.get("key", "?"), why))
            continue
        crop = (r.get("crop") or "").strip()
        r["verified"] = bool(crop) and os.path.exists(os.path.join(raw_dir, crop))
        good[r["key"]] = r
    return good, rejected


def status(ok, *rows):
    """PASS if ok; FAIL only if every reading involved is verified by a crop; else UNCLEAR."""
    if ok:
        return "PASS"
    return "FAIL" if rows and all(r and r.get("verified") for r in rows) else "UNCLEAR"


def confidence(*rows):
    return "high" if rows and all(r and r.get("verified") and r.get("confidence") == "high" for r in rows) else "medium"


def warning(rejected):
    if not rejected:
        return None
    return ("Not used as sheet readings (%d): %s. A table value must be read off the sheet image, never copied from "
            "the model." % (len(rejected), "; ".join("%s (%s)" % kr for kr in rejected)))


def has_crop(r, raw_dir):
    if r.get("verified"):
        return True
    c = (r.get("crop") or "").strip()
    return bool(c) and raw_dir is not None and os.path.exists(os.path.join(raw_dir, c))


def observation(rows, key, raw_dir=None):
    """A judgement read off the sheets (e.g. 'Appendix G table present'): the row's `finding` column says PASS or FAIL.
    Returns (status, actual text, confidence).  No row, or no finding -> UNCLEAR: never assume what was not looked at.
    PASS says the item IS on the sheet: it needs a crop of it.  FAIL says it is NOT there: it names the sheets looked at.
    Without that evidence the judgement stays UNCLEAR (see obs_fix for the fix text)."""
    r = rows.get(key)
    if not r:
        return "UNCLEAR", "not read", "medium"
    fnd = (r.get("finding") or "").strip().upper()
    text = (r.get("value") or "") + (" (%s)" % r["sheet"] if r.get("sheet") else "")
    if fnd not in ("PASS", "FAIL"):
        return "UNCLEAR", text, "medium"
    if fnd == "PASS" and not has_crop(r, raw_dir):
        return "UNCLEAR", text + " - PASS given without a crop", "medium"
    if fnd == "FAIL" and not (r.get("sheet") or "").strip():
        return "UNCLEAR", text + " - FAIL given without the sheets looked at", "medium"
    return fnd, text, r.get("confidence") or "medium"


OBS_FIX = ("A PASS says the item is on the sheet: save a crop of it (`box` + crop_readings.py, or the `crop` column); a "
           "FAIL names the sheets looked at in `sheet`. Until then this stays UNCLEAR.")


def obs_fix(rows, key, raw_dir, default):
    """Fix text for an UNCLEAR judgement: what evidence is missing, or the default (read it / record it)."""
    r = rows.get(key)
    fnd = (r.get("finding") or "").strip().upper() if r else ""
    if (fnd == "PASS" and not has_crop(r, raw_dir)) or (fnd == "FAIL" and not (r.get("sheet") or "").strip()):
        return OBS_FIX
    return default


def listing(rows, raw_dir, keys=None, rejected=()):
    """Every reading for the operator to check: key, sheet, value, finding, confidence, note, crop (absolute path or None)."""
    out = []
    for k, r in rows.items():
        if keys is not None and k not in keys:
            continue
        c = (r.get("crop") or "").strip()
        p = os.path.abspath(os.path.join(raw_dir, c)) if c and raw_dir and os.path.exists(os.path.join(raw_dir, c)) else None
        out.append({"key": k, "sheet": r.get("sheet", ""), "item": r.get("item", ""), "value": r.get("value", ""),
                    "finding": (r.get("finding") or "").strip().upper(), "confidence": r.get("confidence", ""),
                    "note": r.get("note", ""), "crop": p})
    for k, why in rejected:
        out.append({"key": k, "sheet": "", "item": "", "value": "", "finding": "REJECTED", "confidence": "",
                    "note": why, "crop": None})
    return out


CROP_FIX = ("The value read differs from the model but has no crop of the table cell: save one (`crop` column in "
            "table_values.tsv, e.g. with tools/common/crop_readings.py) and re-run. FAIL needs the crop.")
