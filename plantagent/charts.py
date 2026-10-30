"""Small dependency-free SVG line chart for parameter sweeps: utilisation (%) of the tightest checks against one
varied input, with the 100 % limit line. Numbers come from simulator solves; this only draws them."""
import math
from xml.sax.saxutils import escape

PALETTE = ("#2563eb", "#d97706", "#059669", "#7c3aed", "#db2777", "#0891b2")


def sweep_svg(title, x_label, xs, series, w=720, h=380):
    """series: {name: [utilisation fraction or None per x]}. Returns SVG text."""
    pad_l, pad_r, pad_t, pad_b = 64, 190, 44, 52
    vals = [v for s in series.values() for v in s if v is not None] + [1.0]
    y_max = max(1.2, max(vals) * 1.08)
    x0, x1 = min(xs), max(xs)
    sx = lambda x: pad_l + (x - x0) / ((x1 - x0) or 1) * (w - pad_l - pad_r)  # noqa: E731
    sy = lambda y: h - pad_b - y / y_max * (h - pad_t - pad_b)  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{pad_l}" y="24" font-size="15" font-weight="600" fill="#111">{escape(title)}</text>']
    for k in range(0, int(y_max * 100) + 1, 20):  # gridlines every 20 %
        y = sy(k / 100)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" stroke="#eee"/>'
                   f'<text x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" fill="#555">{k}%</text>')
    y100 = sy(1.0)
    out.append(f'<line x1="{pad_l}" y1="{y100:.1f}" x2="{w - pad_r}" y2="{y100:.1f}" stroke="#b91c1c" stroke-dasharray="6,4"/>'
               f'<text x="{pad_l + 6}" y="{y100 - 6:.1f}" fill="#b91c1c">limit 100 %</text>')
    for x in xs:
        out.append(f'<text x="{sx(x):.1f}" y="{h - pad_b + 18}" text-anchor="middle" fill="#555">{x:g}</text>')
    out.append(f'<text x="{(pad_l + w - pad_r) / 2:.1f}" y="{h - 12}" text-anchor="middle" fill="#333">{escape(x_label)}</text>')
    for i, (name, ys) in enumerate(series.items()):
        c = PALETTE[i % len(PALETTE)]
        pts = [(sx(x), sy(y)) for x, y in zip(xs, ys) if y is not None]
        if len(pts) > 1:
            out.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{c}" stroke-width="2"/>')
        out += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{c}"/>' for a, b in pts]
        ly = pad_t + 8 + i * 20
        out.append(f'<line x1="{w - pad_r + 34}" y1="{ly}" x2="{w - pad_r + 50}" y2="{ly}" stroke="{c}" stroke-width="2"/>'
                   f'<text x="{w - pad_r + 55}" y="{ly + 4}" fill="#333">{escape(name[:22])}</text>')
    out.append("</svg>")
    return "\n".join(out)


def fouling_svg(title, f, w=720, h=380):
    """U history (daily means), the fit since cleaning with its 95 % band, the simulator's critical U and the limit date.
    f: plantagent.forecast.forecast() result."""
    from datetime import date, timedelta
    pad_l, pad_r, pad_t, pad_b = 64, 24, 44, 52
    pts, fit = f["points"], f["fit"]
    end = max(pts[-1][0], (f.get("after") or {}).get("day") or 0, f.get("limit_day") or 0) + 2
    ys = [u for _, u in pts] + [f.get("U_critical") or 0]
    y0, y1 = math.floor(min(ys) / 200) * 200 - 200, math.ceil(max(ys + [f.get("U_clean") or 0]) / 200) * 200
    sx = lambda x: pad_l + x / end * (w - pad_l - pad_r)  # noqa: E731
    sy = lambda y: h - pad_b - (y - y0) / (y1 - y0) * (h - pad_t - pad_b)  # noqa: E731
    t0 = date.fromisoformat(f["points_start"]) if f.get("points_start") else None
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{pad_l}" y="24" font-size="15" font-weight="600" fill="#111">{escape(title)}</text>']
    for y in range(int(y0), int(y1) + 1, 200):
        out.append(f'<line x1="{pad_l}" y1="{sy(y):.1f}" x2="{w - pad_r}" y2="{sy(y):.1f}" stroke="#eee"/>'
                   f'<text x="{pad_l - 8}" y="{sy(y) + 4:.1f}" text-anchor="end" fill="#555">{y}</text>')
    for d in range(0, int(end) + 1, 7):
        lab = (t0 + timedelta(days=d)).strftime("%d %b") if t0 else f"day {d}"
        out.append(f'<text x="{sx(d):.1f}" y="{h - pad_b + 18}" text-anchor="middle" fill="#555">{lab}</text>')
    out.append(f'<text x="{(pad_l + w - pad_r) / 2:.1f}" y="{h - 12}" text-anchor="middle" fill="#333">U (W/m²K), daily mean from the historian</text>')
    if f.get("U_critical"):
        yc = sy(f["U_critical"])
        out.append(f'<line x1="{pad_l}" y1="{yc:.1f}" x2="{w - pad_r}" y2="{yc:.1f}" stroke="#b91c1c" stroke-dasharray="6,4"/>'
                   f'<text x="{pad_l + 6}" y="{yc - 6:.1f}" fill="#b91c1c">limit U {f["U_critical"]:.0f} (DWSIM: {escape(f["first_limit"]["id"])} at 100 %)</text>')
    line = lambda s: [(x, fit["mean_U"] + s * (x - fit["mean_day"])) for x in (fit["from_day"], end)]  # noqa: E731
    for s, dash in ((fit["slope_per_day"] - 1.96 * fit["slope_se"], "3,3"), (fit["slope_per_day"] + 1.96 * fit["slope_se"], "3,3"),
                    (fit["slope_per_day"], "")):
        (a, b), (c, d) = line(s)
        out.append(f'<line x1="{sx(a):.1f}" y1="{sy(b):.1f}" x2="{sx(c):.1f}" y2="{sy(d):.1f}" stroke="#d97706" '
                   f'stroke-width="{1 if dash else 2}"{f" stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
    out.append(f'<polyline points="{" ".join(f"{sx(x):.1f},{sy(u):.1f}" for x, u in pts)}" fill="none" stroke="#2563eb" stroke-width="1.5"/>')
    out += [f'<circle cx="{sx(x):.1f}" cy="{sy(u):.1f}" r="2.5" fill="#2563eb"/>' for x, u in pts]
    for day, label, colour in ((f.get("as_of_day"), "today", "#111"), (f.get("limit_day"), f"limit {f.get('limit_date')}", "#b91c1c")):
        if day is not None:
            out.append(f'<line x1="{sx(day):.1f}" y1="{pad_t}" x2="{sx(day):.1f}" y2="{h - pad_b}" stroke="{colour}" stroke-width="1"/>'
                       f'<text x="{sx(day) + 4:.1f}" y="{pad_t + 12 + (14 if label != "today" else 0)}" fill="{colour}">{escape(label)}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    s = sweep_svg("Test", "seawater temperature (C)", [10, 20, 30], {"K-201 suction": [0.9, 1.0, 1.1], "E-201 area": [0.8, None, 1.2]})
    assert s.startswith("<svg") and s.count("<polyline") == 2 and "limit 100 %" in s
    print("ok")
