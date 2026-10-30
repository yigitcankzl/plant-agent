"""CAD in and out: DWG/DXF/vector-PDF drawings -> text, geometry and a Muse reading -> redlined DXF and DWG.

Usage: python -m plantagent.cad   (Pahala P-201 demo + NCSD native DWG check)
"""
import base64
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import ezdxf
import pymupdf
from ezdxf.addons.drawing import matplotlib as dxf_mpl

from . import llm

ODA = Path.home() / "opt/oda/squashfs-root/AppRun"
REV_LAYER = "REV-AGENT"


# --- format conversion -------------------------------------------------------------------------
def oda_convert(src, fmt):
    """DWG <-> DXF with the ODA File Converter (needs an X display; xvfb-run provides one headless)."""
    src = Path(src)
    with tempfile.TemporaryDirectory() as i, tempfile.TemporaryDirectory() as o:
        shutil.copy(src, i)
        subprocess.run(["xvfb-run", "-a", str(ODA), i, o, "ACAD2018", fmt, "0", "1", "*." + src.suffix[1:].upper()],
                       check=True, capture_output=True, timeout=300)
        out = src.with_suffix("." + fmt.lower())
        produced = next(Path(o).glob("*." + fmt.lower()))
        shutil.copy(produced, out)
    return out


def pdf_page_to_dxf(pdf, page, out):
    """Vector PDF sheet (plotted from AutoCAD) -> DXF: every path segment and text span, in PDF points, y up."""
    pg = pymupdf.open(pdf)[page - 1]
    h, m = pg.rect.height, pg.rotation_matrix  # plotted sheets are often stored rotated; work in the viewed orientation
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    P = lambda p: ((p * m).x, h - (p * m).y)  # noqa: E731
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                msp.add_line(P(it[1]), P(it[2]))
            elif it[0] == "c":  # cubic bezier -> short polyline
                pts = [P(q) for q in it[1:5]]
                curve = [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
                               for a, b, c, d in zip(*pts)) for t in (i / 8 for i in range(9))]
                msp.add_lwpolyline(curve)
            elif it[0] == "re":
                r = it[1]
                msp.add_lwpolyline([P(r.tl), P(r.tr), P(r.br), P(r.bl)], close=True)
    for x0, y0, x1, y1, word, *_ in pg.get_text("words"):
        r = pymupdf.Rect(x0, y0, x1, y1) * m
        msp.add_text(word, height=max(min(r.width, r.height), 1) * 0.8, dxfattribs={"insert": (r.x0, h - r.y1)})
    doc.saveas(out)
    return Path(out)


# --- reading -----------------------------------------------------------------------------------
def read(dxf):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    counts = {}
    for e in msp:
        counts[e.dxftype()] = counts.get(e.dxftype(), 0) + 1
    texts = [{"text": e.dxf.text, "x": round(e.dxf.insert.x, 1), "y": round(e.dxf.insert.y, 1)}
             for e in msp.query("TEXT")]
    texts += [{"text": e.plain_text(), "x": round(e.dxf.insert.x, 1), "y": round(e.dxf.insert.y, 1)} for e in msp.query("MTEXT")]
    attribs = [{"block": i.dxf.name, "tag": a.dxf.tag, "value": a.dxf.text} for i in msp.query("INSERT") for a in i.attribs]
    return {"version": doc.dxfversion, "layers": [l.dxf.name for l in doc.layers], "counts": counts,
            "texts": texts, "block_attributes": attribs, "extents": _extents(msp)}


def _extents(msp):
    from ezdxf import bbox
    b = bbox.extents(msp, fast=True)
    return [round(b.extmin.x, 1), round(b.extmin.y, 1), round(b.extmax.x, 1), round(b.extmax.y, 1)]


def render(dxf, png, dpi=110):
    doc = ezdxf.readfile(dxf)
    dxf_mpl.qsave(doc.modelspace(), str(png), bg="#FFFFFF", dpi=dpi)
    return Path(png)


# --- Muse reading ------------------------------------------------------------------------------
READ_PROMPT = """You are reading a P&ID sheet. Most tags are drawn as strokes, so read them from the image.
Text entities extracted from the CAD file (with coordinates) are also given; use them where they exist.
Return JSON only:
{"sheet": {"number": "", "title": ""},
 "equipment": [{"tag": "", "type": "pump|tank|basin|mixer|valve|meter|instrument|blower|other", "description": "",
                "bbox": [x0, y0, x1, y1]}],
 "lines": [{"from": "tag or off-sheet ref", "to": "", "size": "", "service": ""}],
 "off_sheet": [{"label": "", "ref_sheet": ""}],
 "notes": ""}
bbox: fractions (0-1) of the image width/height, origin top-left. Include every equipment symbol, also untagged ones
(e.g. submersible pumps drawn as symbols): give them the tag of their own instruments/motor if shown (e.g. "P-040121"),
otherwise "untagged pump 1". Only report what is on the drawing."""


def identify(png, cad, model="muse-spark-1.3-contributor"):
    url = "data:image/png;base64," + base64.b64encode(Path(png).read_bytes()).decode()
    texts = [t for t in cad["texts"] if t["text"].strip()][:400]
    msg = [{"role": "system", "content": READ_PROMPT},
           {"role": "user", "content": [{"type": "text", "text": "CAD text entities: " + json.dumps(texts)},
                                        {"type": "image_url", "image_url": {"url": url}}]}]
    text = llm.chat(model, msg, temperature=0)
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def cross_check(reading, cad):
    """Which tags the vision reading and the CAD text entities agree on."""
    cad_words = {t["text"].strip().upper() for t in cad["texts"]}
    vision = {e["tag"].upper() for e in reading.get("equipment", []) if e.get("tag")}
    in_cad = {t for t in vision if any(part in cad_words for part in t.replace("-", " ").split())}
    return {"vision_tags": sorted(vision), "confirmed_by_cad_text": sorted(in_cad),
            "vision_only": sorted(vision - in_cad), "cad_text_entities": len(cad["texts"]),
            "note": "Tags drawn as strokes have no CAD text; those are vision-only and need human confirmation."}


PROFILE_PROMPT = """You are reading a plant hydraulic profile drawing. Text is drawn as strokes, so read it from the image.
List every elevation label on the sheet (numbers like 465.98 next to a diamond/arrow marker or a water-surface symbol).
Return JSON only:
{"title": "", "design_flow_note": "the note giving the flow the profile is drawn for, verbatim",
 "flow_path": ["structure names in the order water flows through them"],
 "elevations": [{"value": 0.0, "structure": "", "feature": "water surface|max water surface|weir crest|overflow weir|top of wall|invert|grade|floor|other",
                 "label_text": "text next to the value, verbatim", "bbox": [x0, y0, x1, y1]}],
 "notes": ["every general note, verbatim"]}
bbox: fractions (0-1) of the image width/height, origin top-left, tight around the number. Only report what is drawn."""


def read_profile(pdf, page, model="muse-spark-1.3-contributor", zoom=1.6):
    """Muse reads a stroked-text hydraulic profile sheet. Returns the reading and the PNG it read."""
    pg = pymupdf.open(pdf)[page - 1]
    png = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png")
    url = "data:image/png;base64," + base64.b64encode(png).decode()
    text = llm.chat(model, [{"role": "system", "content": PROFILE_PROMPT},
                            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]}], temperature=0)
    return json.loads(text[text.index("{"): text.rindex("}") + 1]), png


TILE_PROMPT = """This is one tile of a hydraulic profile drawing. Text is drawn as strokes. List every elevation number
(like 465.98 or 432±) fully inside this tile. Return JSON only:
{"labels": [{"value": 0.0, "text": "number as drawn plus any words on the same line", "bbox": [x0, y0, x1, y1]}]}
bbox: fractions (0-1) of this tile's width/height, origin top-left, tight around the number only."""


def locate_labels(pdf, page, cols=3, rows=2, overlap=0.08, zoom=2.5, model="muse-spark-1.3-contributor"):
    """Second, independent reading on zoomed tiles: every elevation number with a precise sheet position.
    Returns [{value, text, bbox (sheet fractions)}]; labels seen in two overlapping tiles are merged."""
    pg = pymupdf.open(pdf)[page - 1]
    W, H = pg.rect.width, pg.rect.height
    from concurrent.futures import ThreadPoolExecutor
    tiles = []
    for r in range(rows):
        for c in range(cols):
            fx0, fy0 = max(c / cols - overlap, 0), max(r / rows - overlap, 0)
            fx1, fy1 = min((c + 1) / cols + overlap, 1), min((r + 1) / rows + overlap, 1)
            clip = pymupdf.Rect(fx0 * W, fy0 * H, fx1 * W, fy1 * H)
            png = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip).tobytes("png")
            tiles.append((fx0, fy0, fx1, fy1, "data:image/png;base64," + base64.b64encode(png).decode()))

    def read_tile(t):  # tiles are read in parallel: the sheet takes one tile's time, not six
        return llm.chat(model, [{"role": "system", "content": TILE_PROMPT},
                                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": t[4]}}]}], temperature=0)
    with ThreadPoolExecutor(len(tiles)) as ex:
        texts = list(ex.map(llm.inherit_tag(read_tile), tiles))
    found = []
    for (fx0, fy0, fx1, fy1, _), text in zip(tiles, texts):
        if True:
            for lab in json.loads(text[text.index("{"): text.rindex("}") + 1]).get("labels", []):
                x0, y0, x1, y1 = lab["bbox"]
                b = [fx0 + x0 * (fx1 - fx0), fy0 + y0 * (fy1 - fy0), fx0 + x1 * (fx1 - fx0), fy0 + y1 * (fy1 - fy0)]
                dup = next((f for f in found if f["value"] == lab["value"] and abs(f["bbox"][0] - b[0]) < 0.02
                            and abs(f["bbox"][1] - b[1]) < 0.02), None)
                if not dup:
                    found.append({"value": lab["value"], "text": lab.get("text", ""), "bbox": [round(v, 4) for v in b]})
    return found


def reconcile(reading, located, tol=0.06):
    """Match the full-sheet reading with the tile reading: same value and nearby position = confirmed by two reads."""
    used, out = set(), []
    for e in reading["elevations"]:
        cx, cy = (e["bbox"][0] + e["bbox"][2]) / 2, (e["bbox"][1] + e["bbox"][3]) / 2
        best = None
        for i, l in enumerate(located):
            if i in used or abs(float(l["value"]) - float(e["value"])) > 1e-6:
                continue
            d = math.hypot((l["bbox"][0] + l["bbox"][2]) / 2 - cx, (l["bbox"][1] + l["bbox"][3]) / 2 - cy)
            if d < tol and (best is None or d < best[1]):
                best = (i, d)
        row = dict(e)
        if best:
            used.add(best[0])
            row["bbox"], row["confirmed"] = located[best[0]]["bbox"], "two reads"
        else:
            row["confirmed"] = "single read - human confirm"
        out.append(row)
    extra = [l for i, l in enumerate(located) if i not in used]
    return out, extra


# --- writing the redline -----------------------------------------------------------------------
def _cloud(msp, x0, y0, x1, y1, arc=None):
    """Revision cloud: a closed polyline of outward bulged arcs around a rectangle."""
    arc = arc or max(min(x1 - x0, y1 - y0) / 6, 4)
    pts = []
    for (ax, ay), (bx, by) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        n = max(int(math.hypot(bx - ax, by - ay) / arc), 1)
        pts += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n, 0, 0, -0.6) for i in range(n)]
    msp.add_lwpolyline(pts, format="xyseb", close=True, dxfattribs={"layer": REV_LAYER, "const_width": 0.8})


def redline(dxf_in, dxf_out, changes, rev, extents, labels=()):
    """changes: [{bbox (image fractions, top-left origin), note}]. Adds clouds, delta tags, notes and a revision table.
    labels: [{bbox, text}] result text written just below an existing label (e.g. the new water surface)."""
    doc = ezdxf.readfile(dxf_in)
    if REV_LAYER not in doc.layers:
        doc.layers.add(REV_LAYER, color=1)  # red
    msp = doc.modelspace()
    ex0, ey0, ex1, ey1 = extents
    W, H = ex1 - ex0, ey1 - ey0
    for i, ch in enumerate(changes, 1):
        fx0, fy0, fx1, fy1 = ch["bbox"]
        x0, x1 = ex0 + fx0 * W, ex0 + fx1 * W
        y0, y1 = ey1 - fy1 * H, ey1 - fy0 * H
        pad = 0.01 * W
        _cloud(msp, x0 - pad, y0 - pad, x1 + pad, y1 + pad)
        msp.add_lwpolyline([(x1 + pad, y1 + pad), (x1 + pad + 18, y1 + pad + 18), (x1 + pad + 6, y1 + pad + 18)],
                           close=True, dxfattribs={"layer": REV_LAYER})  # delta triangle
        msp.add_text(f"{rev['number']}{i}", height=7, dxfattribs={"layer": REV_LAYER, "insert": (x1 + pad + 7, y1 + pad + 3)})
    for lab in labels:
        fx0, fy0, fx1, fy1 = lab["bbox"]
        msp.add_text(lab["text"], height=5, dxfattribs={"layer": REV_LAYER, "insert": (ex0 + fx0 * W, ey1 - fy1 * H - 7)})
    # Revision notes and table, stacked bottom-left of the sheet, outside the title block.
    tx, ty = ex0 + 0.05 * W, ey0 + 0.12 * H
    for i, ch in enumerate(changes, 1):
        msp.add_text(f"{rev['number']}{i}  {ch['note']}", height=6,
                     dxfattribs={"layer": REV_LAYER, "insert": (tx, ty + 12 + 10 * (len(changes) - i))})
    rows = [("REV", "DATE", "DESCRIPTION", "BY"), (rev["number"], rev["date"], rev["description"], rev["by"])]
    widths = [30, 60, 330, 80]
    for r, row in enumerate(rows):
        x = tx
        for w, cell in zip(widths, row):
            msp.add_lwpolyline([(x, ty - 14 * r), (x + w, ty - 14 * r), (x + w, ty - 14 * (r + 1)), (x, ty - 14 * (r + 1))],
                               close=True, dxfattribs={"layer": REV_LAYER})
            msp.add_text(cell, height=6, dxfattribs={"layer": REV_LAYER, "insert": (x + 2, ty - 14 * r - 10)})
            x += w
    doc.saveas(dxf_out)
    return Path(dxf_out)


# --- demo --------------------------------------------------------------------------------------
PAHALA = Path("/home/kizil/Desktop/hackathon/case-data/realcad/pahala/pahala-wwtp-drawings.pdf")
NCSD = Path("/home/kizil/Desktop/hackathon/case-data/realcad/ncsd")


def demo(out=Path("runs/cad")):
    out.mkdir(parents=True, exist_ok=True)
    report = {}

    # 1. Native DWG input: a real utility AutoCAD file -> DXF -> read.
    dwg = next(NCSD.glob("PS-003*.dwg"))
    local = out / dwg.name
    shutil.copy(dwg, local)
    ncsd = read(oda_convert(local, "DXF"))
    report["ncsd_native_dwg"] = {"file": dwg.name, "version": ncsd["version"], "counts": ncsd["counts"],
                                 "sample_texts": [t["text"] for t in ncsd["texts"] if t["text"].strip()][:15]}

    # 2. Pahala P-201 (Anoxic Basin): AutoCAD-plotted vector PDF -> DXF -> DWG -> DXF round trip.
    sheet = out / "pahala_P-201.dxf"
    pdf_page_to_dxf(PAHALA, 10, sheet)
    dwg_rt = oda_convert(sheet, "DWG")
    rt = read(oda_convert(dwg_rt, "DXF"))
    cad = read(sheet)
    report["pahala_cad"] = {"sheet": "P-201", "counts": cad["counts"], "text_entities": len(cad["texts"]),
                            "roundtrip_dwg_counts": rt["counts"]}

    # 3. Muse reads the sheet (vision + CAD text), cross-checked.
    png = out / "pahala_P-201.png"
    page = pymupdf.open(PAHALA)[9]
    clip_w = 0.86  # drawing area without the title block, read at full resolution
    page.get_pixmap(matrix=pymupdf.Matrix(1.0, 1.0), clip=pymupdf.Rect(0, 0, clip_w * page.rect.width, page.rect.height)).save(png)
    reading = identify(png, cad)
    for e in reading.get("equipment", []):
        if e.get("bbox"):
            x0, y0, x1, y1 = e["bbox"]
            e["bbox"] = [x0 * clip_w, y0, x1 * clip_w, y1]  # back to whole-sheet fractions
    report["reading"] = reading
    report["cross_check"] = cross_check(reading, cad)

    # 4. Hydraulic check: the P&ID and the PER give plant flows but no recycle pump ratings or line lengths.
    report["hydraulic_check"] = {
        "status": "not run - insufficient data",
        "have": "PER: peak hour wet weather 630 gpm (EA Vol 2, PER section); P&ID: two submersible recycle pumps, "
                "12x10 and 10x12 reducers around FE-040141, recycle to PA-01 (P-201)",
        "missing": ["recycle pump rating (flow, head) or curve", "recycle line length and diameter",
                    "water levels in anoxic basin and PA-01"],
        "rfi": "Request pump data sheets for the anoxic recycle pumps and the yard piping plan from the design-build contractor."}

    # 5. Redline: clouds around the pumps the reading found, marked as an RFI (no engineering basis for a change).
    pumps = [e for e in reading.get("equipment", []) if e.get("type") == "pump" and e.get("bbox")]
    changes = [{"bbox": p["bbox"], "note": f"ILLUSTRATIVE - RFI: confirm rating of {p.get('tag') or 'recycle pump'} "
                                           "(flow/head not shown on P&ID or PER). No engineering change made."} for p in pumps[:2]]
    rev = {"number": "A", "date": "2026-10-27", "by": "AGENT", "description": "ILLUSTRATIVE REDLINE - RFI CLOUDS, NOT FOR CONSTRUCTION"}
    page_box = [0, 0, page.rect.width, page.rect.height]  # image fractions map onto the sheet, not the entity extents
    red = redline(sheet, out / "pahala_P-201_redline.dxf", changes, rev, page_box)
    red_dwg = oda_convert(red, "DWG")
    back = read(oda_convert(red_dwg, "DXF"))
    render(red, out / "pahala_P-201_redline.png")
    report["redline"] = {"dxf": str(red), "dwg": str(red_dwg), "clouds": len(changes),
                         "rev_layer_in_dwg_roundtrip": REV_LAYER in back["layers"],
                         "rev_texts_after_roundtrip": [t["text"] for t in back["texts"] if "ILLUSTRATIVE" in t["text"] or t["text"] == "A"][:5]}
    (out / "cad_report.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    r = demo()
    print(json.dumps({k: v for k, v in r.items() if k != "reading"}, indent=2)[:4000])
    print("equipment read:", [(e.get("tag"), e.get("type")) for e in r["reading"].get("equipment", [])])
    assert r["redline"]["rev_layer_in_dwg_roundtrip"], "revision layer must survive DXF -> DWG -> DXF"
    print(f"spent ${llm.spent():.4f}")
