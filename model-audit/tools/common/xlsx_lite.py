"""Minimal .xlsx writer, standard library only.

Enough for audit tables: several sheets, bold header row, frozen header,
column widths, number format with 3 decimals, and fill colours for
Pass (green) / Fail (red) / N/A (yellow). No formulas.

    wb = Workbook()
    ws = wb.sheet("Summary", widths=[30, 12])
    ws.row(["Metric", "Value"], header=True)
    ws.row(["Rooms", 66])
    ws.row(["Status", Cell("PASS", fill="pass")])
    wb.save("out.xlsx")
"""
import re
import zipfile
from xml.sax.saxutils import escape

FILLS = {"pass": "FFC6EFCE", "fail": "FFFFC7CE", "na": "FFFFEB9C", "head": "FFD9E1F2", "note": "FFF2F2F2"}
# style index: (fill, bold, number)
_STYLES = [(None, False, False)]


def _style(fill=None, bold=False, num=False):
    key = (fill, bold, num)
    if key not in _STYLES:
        _STYLES.append(key)
    return _STYLES.index(key)


class Cell:
    def __init__(self, value, fill=None, bold=False):
        self.value, self.fill, self.bold = value, fill, bold


def _col(n):
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


class Sheet:
    def __init__(self, name, widths=None, freeze=True):
        self.name = re.sub(r"[\[\]:*?/\\]", "-", name)[:31]
        self.widths = widths or []
        self.freeze = freeze
        self.rows = []

    def row(self, values, header=False, fill=None):
        cells = []
        for v in values:
            c = v if isinstance(v, Cell) else Cell(v)
            if header:
                c.bold, c.fill = True, c.fill or "head"
            elif fill and not c.fill:
                c.fill = fill
            cells.append(c)
        self.rows.append(cells)

    def _xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
        if self.freeze and self.rows:
            out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
                       'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
        if self.widths:
            out.append("<cols>" + "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, w)
                                          for i, w in enumerate(self.widths)) + "</cols>")
        out.append("<sheetData>")
        for ri, cells in enumerate(self.rows, 1):
            out.append('<row r="%d">' % ri)
            for ci, c in enumerate(cells):
                ref = "%s%d" % (_col(ci), ri)
                v = c.value
                if v is None or v == "":
                    s = _style(c.fill, c.bold)
                    out.append('<c r="%s" s="%d"/>' % (ref, s))
                elif isinstance(v, bool):
                    s = _style(c.fill, c.bold)
                    out.append('<c r="%s" s="%d" t="inlineStr"><is><t>%s</t></is></c>' % (ref, s, "Yes" if v else "No"))
                elif isinstance(v, (int, float)):
                    s = _style(c.fill, c.bold, isinstance(v, float))
                    out.append('<c r="%s" s="%d"><v>%s</v></c>' % (ref, s, repr(float(v)) if isinstance(v, float) else v))
                else:
                    s = _style(c.fill, c.bold)
                    t = escape(_BAD.sub("", str(v)))
                    out.append('<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, s, t))
            out.append("</row>")
        out.append("</sheetData>")
        if self.rows:
            out.append('<autoFilter ref="A1:%s%d"/>' % (_col(max(len(r) for r in self.rows) - 1), len(self.rows)))
        out.append("</worksheet>")
        return "".join(out)


class Workbook:
    def __init__(self):
        self.sheets = []

    def sheet(self, name, widths=None, freeze=True):
        ws = Sheet(name, widths, freeze)
        self.sheets.append(ws)
        return ws

    def _styles_xml(self):
        fills = ['<fill><patternFill patternType="none"/></fill>', '<fill><patternFill patternType="gray125"/></fill>']
        fill_ix = {}
        for f, _, _ in _STYLES:
            if f and f not in fill_ix:
                fill_ix[f] = len(fills)
                fills.append('<fill><patternFill patternType="solid"><fgColor rgb="%s"/><bgColor indexed="64"/>'
                             '</patternFill></fill>' % FILLS[f])
        xfs = []
        for f, b, n in _STYLES:
            xfs.append('<xf numFmtId="%d" fontId="%d" fillId="%d" borderId="1" xfId="0" applyBorder="1"%s%s%s>'
                       '<alignment vertical="top" wrapText="1"/></xf>'
                       % (164 if n else 0, 1 if b else 0, fill_ix.get(f, 0),
                          ' applyFill="1"' if f else "", ' applyFont="1"' if b else "",
                          ' applyNumberFormat="1"' if n else ""))
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<numFmts count="1"><numFmt numFmtId="164" formatCode="0.000"/></numFmts>'
                '<fonts count="2"><font><sz val="10"/><name val="Arial"/></font>'
                '<font><b/><sz val="10"/><name val="Arial"/></font></fonts>'
                '<fills count="%d">%s</fills>'
                '<borders count="2"><border/><border><left style="thin"><color rgb="FFBFBFBF"/></left>'
                '<right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top>'
                '<bottom style="thin"><color rgb="FFBFBFBF"/></bottom></border></borders>'
                '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
                '<cellXfs count="%d">%s</cellXfs>'
                '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'
                % (len(fills), "".join(fills), len(xfs), "".join(xfs)))

    def save(self, path):
        sheet_xml = [ws._xml() for ws in self.sheets]   # registers styles first
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                       '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                       '<Default Extension="xml" ContentType="application/xml"/>'
                       '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                       '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                       + "".join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/'
                                 'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1)
                                 for i in range(len(self.sheets))) + "</Types>")
            z.writestr("_rels/.rels",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                       '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                       '</Relationships>')
            z.writestr("xl/workbook.xml",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                       '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                       + "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(ws.name), i + 1, i + 1)
                                 for i, ws in enumerate(self.sheets))
                       + "</sheets>"
                       + "<definedNames>" + "".join(
                           '<definedName name="_xlnm._FilterDatabase" localSheetId="%d" hidden="1">\'%s\'!$A$1:$%s$%d</definedName>'
                           % (i, escape(ws.name).replace("'", "''"), _col(max(len(r) for r in ws.rows) - 1), len(ws.rows))
                           for i, ws in enumerate(self.sheets) if ws.rows) + "</definedNames>"
                       + "</workbook>")
            z.writestr("xl/_rels/workbook.xml.rels",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                       '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       + "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                                 'relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1)
                                 for i in range(len(self.sheets)))
                       + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                         'relationships/styles" Target="styles.xml"/>' % (len(self.sheets) + 1)
                       + "</Relationships>")
            z.writestr("xl/styles.xml", self._styles_xml())
            for i, x in enumerate(sheet_xml):
                z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), x)
