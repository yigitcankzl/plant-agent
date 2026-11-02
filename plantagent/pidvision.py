"""Read a P&ID or HVAC/process schematic that is only a PDF (what most plants have) with Muse vision, into the same
structure as the DEXPI reader (pid.overview): equipment with design data, connections, loops, valves.

Muse reads the topology from the image; positions come from the PDF's own text layer (exact), so the workspace can put
live badges on the real sheet. Scanned sheets without a text layer fall back to Muse's approximate boxes.
"""
import base64
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import pymupdf

from . import llm

S = {"type": "string"}
N = {"type": ["number", "null"]}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["title", "loops", "equipment", "connections", "notes"], "properties": {
    "title": S,
    "loops": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "fluid", "supply_C", "return_C"],
                                         "properties": {"name": S, "fluid": S, "supply_C": N, "return_C": N}}},
    "equipment": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                  "required": ["tag", "label_text", "occurrence", "class", "count", "loops", "capacity_kW", "flow_gpm", "notes", "box"],
                  "properties": {"tag": {"type": "string", "description": "a unique id you assign, e.g. PHE-1, DC-2, RACK-3"},
                                 "label_text": {"type": "string", "description": "the label exactly as printed next to it, e.g. 'PHE' or 'DRY COOLER'"},
                                 "occurrence": {"type": "integer", "description": "which occurrence of that label, counted left to right then top to bottom (1-based)"},
                                 "class": {"type": "string", "description": "plate heat exchanger, dry cooler, pump, tank, CDU, rack, rear-door heat exchanger, chiller, cooling tower, ..."},
                                 "count": {"type": "integer"}, "loops": {"type": "array", "items": S},
                                 "capacity_kW": N, "flow_gpm": N, "notes": S,
                                 "box": {"type": "array", "items": {"type": "number"}, "description": "approximate [x0,y0,x1,y1] as fractions of the image"}}}},
    "connections": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["from", "to", "loop", "inline"],
                    "properties": {"from": S, "to": S, "loop": S, "inline": {"type": "array", "items": S}}}},
    "notes": {"type": "array", "items": S}}}

PROMPT = ("You are a mechanical/process engineer reading a schematic drawing. List every loop (fluid and supply/return "
          "temperatures as printed), every equipment item (give each a unique tag; capacity and flow only as printed), and every "
          "equipment-to-equipment connection with the loop it belongs to and the valve types inline (as printed: BFV, NRV, MBFV, "
          "PICV, Y-ST...). Group identical repeated items (e.g. 14 rear-door heat exchangers) as one entry with count. Do not invent "
          "values. The printed text labels with their positions are given to help you locate items.")


def _labels(page):
    """Printed text lines with their boxes (PDF points)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            t = " ".join(s["text"] for s in ln["spans"]).strip()
            if t:
                out.append({"text": t, "bbox": [round(v, 1) for v in ln["bbox"]]})
    return out


def render(pdf, page=0, dpi=170, rotate=0):
    doc = pymupdf.open(str(pdf))
    pg = doc[page]
    if rotate:
        pg.set_rotation(rotate)
    return pg.get_pixmap(dpi=dpi).tobytes("png")


def read(pdf, page=0, model="muse-spark-1.3-contributor", rotate=0, sam_assisted=None, sam_dir=None):
    doc = pymupdf.open(str(pdf))
    pg = doc[page]
    if rotate:  # a sheet drawn sideways (patent figures) is read upright
        pg.set_rotation(rotate)
    W, H = pg.rect.width, pg.rect.height
    labels = _labels(pg)
    png = pg.get_pixmap(dpi=170).tobytes("png")
    hint = [{"text": x["text"], "x": round(x["bbox"][0] / W, 3), "y": round(x["bbox"][1] / H, 3)} for x in labels
            if not x["text"].replace(" ", "").isdigit()][:400]
    msg = [{"role": "system", "content": PROMPT},
           {"role": "user", "content": [
               {"type": "text", "text": "Printed labels (x, y as fractions of the sheet): " + json.dumps(hint)},
               {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}]}]
    assisted = os.getenv("PID_SAM") == "1" if sam_assisted is None else sam_assisted
    manifest = None
    if assisted:
        from . import sam
        folder = Path(sam_dir) if sam_dir else llm.ROOT / "runs" / "pid_sam" / hashlib.sha256(png).hexdigest()
        segmentation = sam.segment(png, ["pump", "heat exchanger", "vessel", "compressor", "valve", "pipe"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "segments.json").write_text(json.dumps(segmentation, indent=2))
        manifest = sam.assistance(png, segmentation, folder)
        msg[1]["content"].extend(sam_content(manifest, folder))
    params = {"response_format": {"type": "json_schema", "json_schema": {"name": "schematic", "schema": SCHEMA, "strict": True}}}
    if assisted:
        params["max_tokens"] = 6000
    m = llm.complete(model, msg, **params)
    if assisted and not isinstance(m.get("content"), str):
        (folder / "read_failure.json").write_text(json.dumps({"model": model, "message": m,
            "error": "Vision model returned no JSON content; no retry made."}, indent=2))
        raise ValueError("SAM-assisted vision read returned no JSON content; response saved in read_failure.json")
    r = json.loads(m["content"])
    # positions from the PDF text layer: the k-th occurrence of a label, left to right then top to bottom
    by_text = defaultdict(list)
    for x in labels:
        by_text[x["text"].upper()].append(x["bbox"])
    for k in by_text:
        by_text[k].sort(key=lambda b: (round(b[0] / 40), b[1]))
    positions = {}
    for e in r["equipment"]:
        hits = by_text.get(e["label_text"].upper().strip(), [])
        if 0 < e["occurrence"] <= len(hits):
            b = hits[e["occurrence"] - 1]
            positions[e["tag"]] = {"box": [b[0] / W, b[1] / H, b[2] / W, b[3] / H], "source": "pdf text"}
        elif len(e.get("box") or []) == 4:
            positions[e["tag"]] = {"box": e["box"], "source": "muse estimate"}
    return {"title": r["title"], "loops": r["loops"], "raw": r, "positions": positions, "model": model, "sheet": [W, H],
            **({"sam": manifest} if manifest is not None else {}),
            **overview_of(r)}


def sam_content(manifest, folder):
    """SAM supplies geometry hints, never confirmed tags or topology answers."""
    if not manifest["regions"]:
        return [{"type": "text", "text": "SAM 3.1 returned zero regions for the requested equipment and pipe concepts. "
                 "No masks or crops provide spatial hints. Read the original drawing independently."}]
    text = ("Optional SAM 3.1 segmentation hints follow. The first image is still the original drawing; "
            "the next is a numbered mask overlay, then a sheet of context crops. "
            "SAM concepts are unverified guesses, not equipment types or confirmed connections. "
            "Trace each pipe and arrow on the original; crossings do not imply junctions. "
            "Coordinates are source-image pixels and fractions; keep output boxes in full-sheet fractions. "
            "Do not omit equipment or pipes merely because SAM found no region. Regions: " + json.dumps(manifest))
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode((Path(folder) / name).read_bytes()).decode()}}
        for name in ("overlay.jpg", "crops.jpg")]


def overview_of(r):
    """Shape a vision read like pid.overview so the model builder, coverage check and UI work unchanged."""
    cls = {e["tag"]: e["class"] for e in r["equipment"]}
    eq = [{"tag": e["tag"], "id": e["tag"], "class": e["class"],
           "design": {k: v for k, v in (("capacity_kW", e["capacity_kW"]), ("flow_gpm", e["flow_gpm"]), ("count", e["count"]),
                                       ("loops", ", ".join(e["loops"])), ("label", e["label_text"]), ("notes", e["notes"])) if v not in (None, "", 1)},
           "design_limits": []} for e in r["equipment"]]
    conns = [{"from": f"{c['from']}({cls.get(c['from'], '?')})", "to": f"{c['to']}({cls.get(c['to'], '?')})", "lines": [c["loop"]],
              "inline": c["inline"]} for c in r["connections"]]
    return {"equipment": eq, "connections": conns, "lines": [{"line": lp["name"], "fluid_code": lp["fluid"], "supply_C": lp["supply_C"],
                                                              "return_C": lp["return_C"]} for lp in r["loops"]],
            "valves": [], "control": [], "data_quality": [], "read_notes": r["notes"]}
