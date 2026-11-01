"""Read a vendor data sheet or curve (PDF or image) into the inputs files, with Muse vision.

Muse reads what is printed (value, unit, page, the label it read it from) into a fixed schema; Python converts the units,
checks the reading for physical sense and refuses it when it fails. Nothing is applied until the engineer confirms the table
(assumptions.apply_datasheet), and then it goes through the same CSV path as a typed upload, so the checks use it
(inputs > case > draft) and every value keeps "datasheet" provenance with its page and label.
"""
import base64
import io
import json
import re

from . import llm

PAGES = 3  # data sheets put the rated point on page 1 and the curve on page 2; more pages cost tokens, not accuracy

_Q = {"type": "object", "additionalProperties": False, "required": ["value", "unit", "page", "label"],
      "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": "string"},
                     "page": {"type": "integer", "description": "1-based page the value is printed on"},
                     "label": {"type": "string", "description": "the printed label next to the value, verbatim"}}}
SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["equipment", "model", "tag", "rated", "curve", "unreadable"],
          "properties": {
              "equipment": {"type": "string", "enum": ["pump", "compressor", "motor", "exchanger", "other"]},
              "model": {"type": "string", "description": "manufacturer model / curve number as printed"},
              "tag": {"type": "string", "description": "plant tag if printed, else empty"},
              "rated": {"type": "object", "additionalProperties": False,
                        "required": ["flow", "head", "efficiency", "shaft_power", "motor_power", "speed", "min_flow", "shutoff_head", "voltage"],
                        "properties": {k: _Q for k in ("flow", "head", "efficiency", "shaft_power", "motor_power", "speed",
                                                         "min_flow", "shutoff_head", "voltage")}},
              "curve": {"type": "array", "description": "points read off the head-flow curve at the rated speed/diameter, flow rising",
                        "items": {"type": "object", "additionalProperties": False, "required": ["flow", "head", "efficiency_pct"],
                                  "properties": {"flow": {"type": "number"}, "head": {"type": "number"},
                                                 "efficiency_pct": {"type": ["number", "null"]}}}},
              "curve_units": {"type": "object", "additionalProperties": False, "required": ["flow", "head", "page"],
                              "properties": {"flow": {"type": "string"}, "head": {"type": "string"}, "page": {"type": "integer"}}},
              "unreadable": {"type": "array", "items": {"type": "string"}}}}
SCHEMA["required"].append("curve_units")

PROMPT = ("You read an equipment data sheet or vendor performance curve for a process engineer. Report only what is printed. "
          "For every rated value give the number, its unit as printed, the 1-based page and the printed label next to it; "
          "use value null when it is not on the sheet. Rated power at the pump shaft is shaft_power; the driver nameplate "
          "rating is motor_power. min_flow is the minimum continuous stable flow (MCSF). shutoff_head is the head at zero flow. "
          "If a head-flow curve is drawn, read 5 to 8 points off the curve for the rated speed and impeller, flow rising from "
          "shutoff, with efficiency where an efficiency curve is drawn; give their units and page in curve_units. "
          "Never guess a value that is not printed; list anything you could not read in unreadable.")

# unit -> factor to SI-ish working units: flow m3/h, head m, power kW, speed rpm, voltage kV
_FLOW = {"m3/h": 1, "m³/h": 1, "m3/hr": 1, "usgpm": 0.227125, "gpm": 0.227125, "usgal/min": 0.227125, "l/s": 3.6, "lps": 3.6,
         "l/min": 0.06, "m3/s": 3600, "m3/min": 60}
_HEAD = {"m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1, "ft": 0.3048, "feet": 0.3048, "foot": 0.3048}
_POWER = {"kw": 1, "hp": 0.7457, "bhp": 0.7457, "w": 0.001, "mw": 1000}
_VOLT = {"kv": 1, "v": 0.001}


def _unit(table, unit):
    """Factor for a printed unit. Muse sometimes returns the whole axis title ('USgpm | Head - ft | ...'): read the first
    segment only, and match whole tokens, never substrings ('m' must not match 'mm' or 'ft | Flow - m3/h')."""
    seg = re.split(r"[|,;(]", (unit or "").lower())[0]
    k = seg.strip().replace(" ", "").replace(".", "")
    if k in table:
        return table[k]
    return next((table[t] for t in re.findall(r"[a-z0-9/³]+", seg.replace(".", "")) if t in table), None)


TAG = re.compile(r"[A-Z]{1,4}-?\d{2,5}[A-Z]?")


def _conv(q, table):
    if not q or q.get("value") is None:
        return None
    f = _unit(table, q.get("unit"))
    return round(q["value"] * f, 4) if f else None


def _png_pages(data):
    """PNG bytes of each page of a PDF (first PAGES), or the image itself."""
    if data[:5] == b"%PDF-":
        import pymupdf
        doc = pymupdf.open(stream=data, filetype="pdf")
        return [doc[i].get_pixmap(dpi=130).tobytes("png") for i in range(min(PAGES, doc.page_count))], \
            "\n".join(doc[i].get_text() for i in range(min(PAGES, doc.page_count)))[:6000]
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((1800, 1800))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return [buf.getvalue()], ""


def normalise(raw):
    """Convert Muse's printed reading to working units and run the plausibility checks. Pure function (tested)."""
    r = raw.get("rated") or {}
    rated = {"flow_m3h": _conv(r.get("flow"), _FLOW), "head_m": _conv(r.get("head"), _HEAD),
             "shaft_kw": _conv(r.get("shaft_power"), _POWER), "motor_kw": _conv(r.get("motor_power"), _POWER),
             "min_flow_m3h": _conv(r.get("min_flow"), _FLOW), "shutoff_head_m": _conv(r.get("shutoff_head"), _HEAD),
             "voltage_kv": _conv(r.get("voltage"), _VOLT),
             "speed_rpm": (r.get("speed") or {}).get("value")}
    eff = (r.get("efficiency") or {}).get("value")
    rated["efficiency"] = None if eff is None else round(eff / 100 if eff > 1 else eff, 4)
    cu = raw.get("curve_units") or {}
    fq, fh = _unit(_FLOW, cu.get("flow")), _unit(_HEAD, cu.get("head"))
    curve = [{"flow_m3h": round(p["flow"] * fq, 3), "head_m": round(p["head"] * fh, 3),
              "efficiency_pct": p.get("efficiency_pct")} for p in raw.get("curve") or []] if fq and fh else []
    where = {k: {"page": (r.get(src) or {}).get("page"), "label": (r.get(src) or {}).get("label")}
             for k, src in (("flow_m3h", "flow"), ("head_m", "head"), ("efficiency", "efficiency"), ("shaft_kw", "shaft_power"),
                            ("motor_kw", "motor_power"), ("speed_rpm", "speed"), ("min_flow_m3h", "min_flow"),
                            ("shutoff_head_m", "shutoff_head"), ("voltage_kv", "voltage")) if rated.get(k) is not None}
    checks = []

    def chk(name, ok, note):
        checks.append({"check": name, "status": "ok" if ok else "fail", "note": note})

    for k, src in (("flow_m3h", "flow"), ("head_m", "head"), ("shaft_kw", "shaft_power"), ("motor_kw", "motor_power")):
        q = r.get(src) or {}
        if q.get("value") is not None and rated[k] is None:
            chk(f"unit of {src}", False, f"unit '{q.get('unit')}' is not one PlantAgent converts")
    if rated["efficiency"] is not None:
        chk("efficiency", 0 < rated["efficiency"] <= 1, f"efficiency {rated['efficiency']:.3f} must be between 0 and 1")
    if raw.get("curve") and not curve:
        chk("curve units", False, f"curve units '{cu.get('flow')}' / '{cu.get('head')}' not recognised")
    if curve:
        flows, heads = [p["flow_m3h"] for p in curve], [p["head_m"] for p in curve]
        chk("curve flow rises", all(b > a for a, b in zip(flows, flows[1:])), "curve flow must rise from point to point")
        # head falls with flow; 3 % allowance for a flat top and reading off a drawn line
        chk("head falls with flow", all(b <= a * 1.03 for a, b in zip(heads, heads[1:])) and heads[-1] < heads[0],
            "a centrifugal head-flow curve must fall as flow rises")
        if rated["flow_m3h"] and rated["head_m"] and flows[0] <= rated["flow_m3h"] <= flows[-1]:
            h = next(h0 + (h1 - h0) * (rated["flow_m3h"] - q0) / (q1 - q0)
                     for (q0, h0), (q1, h1) in zip(zip(flows, heads), zip(flows[1:], heads[1:])) if q0 <= rated["flow_m3h"] <= q1)
            chk("rated point on the curve", abs(h - rated["head_m"]) <= 0.10 * rated["head_m"],
                f"curve gives {h:.1f} m at the rated flow vs the rated {rated['head_m']:.1f} m (10 % allowed)")
    if raw.get("equipment") == "pump" and all(rated.get(k) for k in ("flow_m3h", "head_m", "efficiency", "shaft_kw")):
        # water-like density unless printed otherwise: P = rho g Q H / eta
        calc = 1000 * 9.81 * rated["flow_m3h"] / 3600 * rated["head_m"] / rated["efficiency"] / 1000
        chk("shaft power vs rho g Q H / eta", abs(calc - rated["shaft_kw"]) <= 0.30 * rated["shaft_kw"],
            f"{calc:.1f} kW from flow, head and efficiency vs {rated['shaft_kw']:.1f} kW printed (30 % allowed, water density)")
    if raw.get("equipment") in ("pump", "compressor") and not (rated["flow_m3h"] and (rated["head_m"] or curve)):
        chk("rated point", False, "no rated flow and head could be read")
    ok = not any(c["status"] == "fail" for c in checks)
    tag = str(raw.get("tag") or "").strip()
    return {"equipment": raw.get("equipment"), "model": raw.get("model", ""), "tag": tag if TAG.fullmatch(tag) else "", "rated": rated,
            "where": where, "curve": curve, "curve_page": cu.get("page"), "unreadable": raw.get("unreadable") or [],
            "checks": checks, "ok": ok,
            "refused": None if ok else "; ".join(f"{c['check']}: {c['note']}" for c in checks if c["status"] == "fail")}


def read(data, model, filename="datasheet"):
    """Muse vision reading of a data sheet (PDF pages or an image), normalised and checked."""
    pngs, text = _png_pages(data)
    llm.set_tag("datasheet:" + filename[:40])
    content = [{"type": "text", "text": "Read this data sheet." + (f" Its text layer, for exact digits:\n{text}" if text else "")}]
    content += [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(p).decode()}} for p in pngs]
    m = llm.complete(model, [{"role": "system", "content": PROMPT}, {"role": "user", "content": content}],
                     response_format={"type": "json_schema", "json_schema": {"name": "datasheet", "schema": SCHEMA, "strict": True}})
    t = m["content"] or "{}"
    raw = json.loads(t[t.index("{"): t.rindex("}") + 1])
    return {**normalise(raw), "raw": raw, "model_used": model, "pages": len(pngs)}


def to_csv(reading, tag, source):
    """The confirmed reading as the CSV text of the typed uploads (curves / motors), with its source as the note line."""
    note = f"# {source}"
    out = {}
    rated, curve = reading["rated"], list(reading.get("curve") or [])
    if reading.get("equipment") in ("pump", "compressor"):
        pts = curve
        if not pts and rated.get("flow_m3h") and rated.get("head_m"):
            pts = [{"flow_m3h": rated["flow_m3h"], "head_m": rated["head_m"], "efficiency_pct": None}]
            if rated.get("shutoff_head_m"):
                pts.insert(0, {"flow_m3h": 0.0, "head_m": rated["shutoff_head_m"], "efficiency_pct": None})
        if rated.get("min_flow_m3h") and pts and pts[0]["flow_m3h"] < rated["min_flow_m3h"]:
            # the lowest-flow row is the minimum-flow point in the curves template: start the curve at the vendor's MCSF
            q0 = rated["min_flow_m3h"]
            above = [p for p in pts if p["flow_m3h"] > q0]
            below = [p for p in pts if p["flow_m3h"] <= q0][-1]
            nxt = above[0] if above else None
            t = 0 if not nxt else (q0 - below["flow_m3h"]) / (nxt["flow_m3h"] - below["flow_m3h"])
            lerp = lambda a, b: a if b is None or a is None else a + (b - a) * t  # noqa: E731
            pts = [{"flow_m3h": q0, "head_m": round(lerp(below["head_m"], (nxt or {}).get("head_m")), 3),
                    "efficiency_pct": None if below.get("efficiency_pct") is None or not nxt or nxt.get("efficiency_pct") is None
                    else round(lerp(below["efficiency_pct"], nxt["efficiency_pct"]), 1)}] + above
        if len(pts) >= 3:
            rows = ["tag,flow_m3h,head_m,efficiency_pct"] + [
                f"{tag},{p['flow_m3h']:g},{p['head_m']:g},{'' if p.get('efficiency_pct') is None else p['efficiency_pct']}" for p in pts]
            out["curves"] = "\n".join([note] + rows) + "\n"
    kw = rated.get("motor_kw") or rated.get("shaft_kw")
    if kw:
        out["motors"] = "\n".join([note, "tag,kw" + (",voltage_kv" if rated.get("voltage_kv") else ""),
                                   f"{tag},{kw:g}" + (f",{rated['voltage_kv']:g}" if rated.get("voltage_kv") else "")]) + "\n"
    return out
