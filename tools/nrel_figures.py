"""NREL 2011 ethanol figures: parity of the Muse-built DWSIM areas against the report's stream tables, and a block map of
the nine areas coloured by status. Deterministic: reads runs/ws/<area>/comparison.json (tools/nrel_compare.py) and the
feasibility table in runs/ws/nrel_ethanol/STATUS.md. No LLM.

python tools/nrel_figures.py            # write docs/img/nrel_*.svg
python tools/nrel_figures.py --save     # also store them as workspace artifacts (kind "analysis")"""
import json
import math
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
AREAS = {"nrel_ethanol_a300": "A300", "nrel_ethanol_a500": "A500"}
NOTE = "Report values are NREL's Aspen Plus model (Humbird et al. 2011, Appendix E), not plant measurements; " \
       "sugars, polymers and solids are mass-equivalent DWSIM stand-in compounds."
COL = {"3": "#059669", "5": "#d97706", "out": "#b91c1c"}


def comparison(case):
    return json.loads((ROOT / "runs" / "ws" / case / "comparison.json").read_text())


def _points(c):
    """Flow checks (kg/h) only: temperatures are a K difference and are counted in the caption, not plotted."""
    return [(k["report"], k["model"], "3" if k["within_3"] else "5" if k["within_5"] else "out", s["stream"], k["check"])
            for s in c["streams"] for k in s.get("checks", []) if "kg/h" in k["check"] and k["report"] > 0 and k["model"] > 0]


def _caption(area, c):
    s = c["summary"]
    temps = sum(1 for x in c["streams"] for k in x.get("checks", []) if "temperature" in k["check"])
    return (f"{area}: {s['within_5']} of {s['checks']} checks within 5 % ({s['within_3']} within 3 %); "
            f"{s['streams_compared']} streams, {temps} of the checks are temperatures (within 3 K / 5 K)")


def parity_svg(title, sets, w=760, h=640):
    """sets: [(area label, comparison dict)]. Log-log parity of report vs model flows with the ±5 % band."""
    pts = [(a, p) for a, c in sets for p in _points(c)]
    lo = 10 ** math.floor(math.log10(min(min(p[0], p[1]) for _, p in pts)))
    hi = 10 ** math.ceil(math.log10(max(max(p[0], p[1]) for _, p in pts)))
    pad_l, pad_r, pad_t, pad_b = 74, 30, 52, 92 + 16 * len(sets)
    side = min(w - pad_l - pad_r, h - pad_t - pad_b)
    L0, L1 = math.log10(lo), math.log10(hi)
    sx = lambda v: pad_l + (math.log10(v) - L0) / (L1 - L0) * side  # noqa: E731
    sy = lambda v: pad_t + side - (math.log10(v) - L0) / (L1 - L0) * side  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{pad_l}" y="26" font-size="15" font-weight="600" fill="#111">{escape(title)}</text>']
    for e in range(int(L0), int(L1) + 1):  # decade gridlines
        v = 10 ** e
        out.append(f'<line x1="{sx(v):.1f}" y1="{pad_t}" x2="{sx(v):.1f}" y2="{pad_t + side}" stroke="#eee"/>'
                   f'<line x1="{pad_l}" y1="{sy(v):.1f}" x2="{pad_l + side}" y2="{sy(v):.1f}" stroke="#eee"/>'
                   f'<text x="{sx(v):.1f}" y="{pad_t + side + 16}" text-anchor="middle" fill="#555">{v:,.0f}</text>'
                   f'<text x="{pad_l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end" fill="#555">{v:,.0f}</text>')
    band = " ".join(f"{sx(v):.1f},{sy(v * f):.1f}" for f, vs in ((1.05, (lo, hi / 1.05)), (0.95, (hi, lo / 0.95))) for v in vs)
    out.append(f'<polygon points="{band}" fill="#d1fae5" opacity="0.7"/>')
    out.append(f'<line x1="{sx(lo):.1f}" y1="{sy(lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}" stroke="#374151" stroke-dasharray="5,4"/>')
    out.append(f'<text x="{sx(hi) - 4:.1f}" y="{sy(hi) + 14:.1f}" text-anchor="end" fill="#374151">model = report (shaded ±5 %)</text>')
    shapes = {"A300": "circle", "A500": "square"}
    for a, (r, m, k, stream, check) in pts:
        x, y, c = sx(r), sy(min(max(m, lo), hi)), COL[k]
        tip = f"<title>{escape(a)} S{escape(stream)} {escape(check)}: report {r:,.0f}, model {m:,.0f}</title>"
        out.append(f'<rect x="{x - 3.5:.1f}" y="{y - 3.5:.1f}" width="7" height="7" fill="{c}" fill-opacity="0.85">{tip}</rect>'
                   if shapes.get(a) == "square" else f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c}" fill-opacity="0.85">{tip}</circle>')
    out.append(f'<text x="{pad_l + side / 2:.1f}" y="{pad_t + side + 36}" text-anchor="middle" fill="#333">NREL report stream table (kg/h)</text>'
               f'<text transform="translate(18,{pad_t + side / 2:.1f}) rotate(-90)" text-anchor="middle" fill="#333">Muse-built DWSIM model (kg/h)</text>')
    lx = pad_l + side + 14
    for i, (k, lab) in enumerate((("3", "within 3 %"), ("5", "within 5 %"), ("out", "outside 5 %"))):
        out.append(f'<circle cx="{lx + 5}" cy="{pad_t + 10 + i * 18}" r="4" fill="{COL[k]}"/><text x="{lx + 14}" y="{pad_t + 14 + i * 18}" fill="#333">{lab}</text>')
    if len(sets) > 1:
        out.append(f'<circle cx="{lx + 5}" cy="{pad_t + 72}" r="4" fill="#666"/><text x="{lx + 14}" y="{pad_t + 76}" fill="#333">A300</text>'
                   f'<rect x="{lx + 1.5}" y="{pad_t + 86.5}" width="7" height="7" fill="#666"/><text x="{lx + 14}" y="{pad_t + 94}" fill="#333">A500</text>')
    y = pad_t + side + 60
    for a, c in sets:
        out.append(f'<text x="{pad_l}" y="{y}" font-weight="600" fill="#111">{escape(_caption(a, c))}</text>')
        y += 16
    for i, part in enumerate(NOTE.split("; ")):
        out.append(f'<text x="{pad_l}" y="{y + 2 + i * 14}" fill="#555" font-size="11">{escape(part)}</text>')
    y += 14
    if any(a == "A500" for a, _ in sets):
        out.append(f'<text x="{pad_l}" y="{y + 17}" fill="#555" font-size="11">A500 after Muse\'s calibration session (rev 1) and one recorded engineer correction (rev 2, D-502 boilup); heat duties not plotted (0 of 7 within 10 %).</text>')
    out.append("</svg>")
    return "\n".join(out)


def status_table():
    """{area code: (verdict, why)} from the feasibility table in runs/ws/nrel_ethanol/STATUS.md."""
    text = (ROOT / "runs" / "ws" / "nrel_ethanol" / "STATUS.md").read_text()
    rows = {}
    for m in re.finditer(r"^\| (A\d00) ([^|]*)\| ([^|]*)\| ([^|]*)\|$", text, re.M):
        rows[m.group(1)] = (m.group(2).strip(), m.group(3).replace("**", "").strip(), m.group(4).strip())
    return rows


def _kind(verdict):
    v = verdict.lower()
    return "built" if "built by muse" in v else "no" if "not feasible" in v else "feasible" if "feasible" in v or "partial" in v else "na"


FILL = {"built": ("#d1fae5", "#059669", "built by Muse"), "feasible": ("#fef3c7", "#d97706", "feasible in DWSIM, not built"),
        "no": ("#fee2e2", "#b91c1c", "not feasible in DWSIM"), "na": ("#f3f4f6", "#6b7280", "no process simulation needed")}
POS = {"A100": (30, 120), "A200": (260, 120), "A300": (490, 120), "A500": (720, 120), "A700": (950, 120),
       "A400": (490, 320), "A600": (720, 320), "A800": (950, 320), "A900": (260, 320)}
FLOWS = [("A100", "A200", "stover"), ("A200", "A300", "slurry"), ("A300", "A500", "beer"),
         ("A500", "A700", "ethanol"), ("A400", "A300", "enzyme"), ("A500", "A600", "stillage water"),
         ("A500", "A800", "lignin solids"), ("A600", "A800", "biogas, sludge")]


def map_svg(rows, counts, w=1150, h=520, bw=170, bh=110):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#374151"/></marker></defs>',
           '<text x="40" y="30" font-size="15" font-weight="600" fill="#111">NREL 2011 cellulosic ethanol plant (2,000 dry t/d corn stover): nine areas</text>',
           '<text x="40" y="50" fill="#555">Block flow after Humbird et al. 2011 (NREL/TP-5100-47764); status from runs/ws/nrel_ethanol/STATUS.md</text>']
    cx = lambda a: (POS[a][0] + bw / 2, POS[a][1] + bh / 2)  # noqa: E731
    for a, b, lab in FLOWS:
        (x1, y1), (x2, y2) = cx(a), cx(b)
        if y1 == y2:
            x1, x2 = (x1 + bw / 2, x2 - bw / 2) if x2 > x1 else (x1 - bw / 2, x2 + bw / 2)
        elif x1 == x2:
            y1, y2 = (y1 + bh / 2, y2 - bh / 2) if y2 > y1 else (y1 - bh / 2, y2 + bh / 2)
        else:
            y1, y2 = y1 + bh / 2, y2 - bh / 2
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#374151" stroke-width="1.6" marker-end="url(#ar)"/>' +
                   (f'<text x="{(x1 + x2) / 2:.0f}" y="{y1 - 8:.0f}" text-anchor="middle" fill="#374151" font-size="10.5">{escape(lab)}</text>' if y1 == y2 else
                    f'<text x="{(x1 + x2) / 2 + 6:.0f}" y="{(y1 + y2) / 2:.0f}" fill="#374151" font-size="10.5">{escape(lab)}</text>'))
    for a, (x, y) in POS.items():
        name, verdict, why = rows.get(a, ("", "not in status table", ""))
        fill, stroke, _ = FILL[_kind(verdict)]
        out.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                   f'<text x="{x + 8}" y="{y + 18}" font-weight="700" fill="#111">{a}</text>'
                   f'<text x="{x + 8}" y="{y + 34}" fill="#111" font-size="11.5">{escape(name)}</text>')
        lines = [counts[a]] if a in counts else []
        lines += re.findall(r".{1,28}(?:\s|$)", why)[:5] if _kind(verdict) != "built" else []
        for i, t in enumerate(lines[:4]):
            out.append(f'<text x="{x + 8}" y="{y + 52 + i * 14}" fill="{stroke}" font-size="10.5">{escape(t.strip())}</text>')
    for i, (k, (fill, stroke, lab)) in enumerate(FILL.items()):
        out.append(f'<rect x="{30 + i * 260}" y="{h - 40}" width="14" height="14" fill="{fill}" stroke="{stroke}"/><text x="{50 + i * 260}" y="{h - 29}" fill="#333">{escape(lab)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def build():
    comps = {AREAS[c]: comparison(c) for c in AREAS}
    counts = {a: f"{c['summary']['within_5']} of {c['summary']['checks']} checks within 5 %" for a, c in comps.items()}
    figs = {f"nrel_parity_{a.lower()}.svg": parity_svg(f"NREL {a}: Muse-built DWSIM model vs report stream tables", [(a, c)])
            for a, c in comps.items()}
    figs["nrel_parity.svg"] = parity_svg("NREL A300 + A500: Muse-built DWSIM models vs report stream tables", list(comps.items()))
    figs["nrel_plant_map.svg"] = map_svg(status_table(), counts)
    return figs, comps


def main(save=False):
    figs, comps = build()
    out = ROOT / "docs" / "img"
    out.mkdir(parents=True, exist_ok=True)
    for name, svg in figs.items():
        (out / name).write_text(svg)
    if save:
        sys.path.insert(0, str(ROOT))
        from plantagent import artifacts
        src = ["cases/nrel_ethanol/outcome.json (withheld stream tables)", "tools/nrel_compare.py", "runs/ws/nrel_ethanol/STATUS.md"]
        for case, a in AREAS.items():
            artifacts.save(case, "analysis", f"NREL {a} parity vs report", {"parity.svg": figs[f"nrel_parity_{a.lower()}.svg"]},
                           by="tools/nrel_figures.py", sources=src, summary=_caption(a, comps[a]))
        for case in ("nrel_ethanol", *AREAS):
            artifacts.save(case, "analysis", "NREL plant map: nine areas by status", {"plant_map.svg": figs["nrel_plant_map.svg"]},
                           by="tools/nrel_figures.py", sources=src[2:], summary="A300 and A500 built by Muse; A800 not feasible in DWSIM")
        artifacts.save("nrel_ethanol", "analysis", "NREL A300 + A500 parity vs report", {"parity.svg": figs["nrel_parity.svg"]},
                       by="tools/nrel_figures.py", sources=src, summary="; ".join(_caption(a, c) for a, c in comps.items()))
    for a, c in comps.items():
        print(_caption(a, c))
    print("wrote", ", ".join(sorted(figs)))


if __name__ == "__main__":
    main("--save" in sys.argv)
