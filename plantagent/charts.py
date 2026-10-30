"""Small dependency-free SVG line chart for parameter sweeps: utilisation (%) of the tightest checks against one
varied input, with the 100 % limit line. Numbers come from simulator solves; this only draws them."""
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


if __name__ == "__main__":
    s = sweep_svg("Test", "seawater temperature (C)", [10, 20, 30], {"K-201 suction": [0.9, 1.0, 1.1], "E-201 area": [0.8, None, 1.2]})
    assert s.startswith("<svg") and s.count("<polyline") == 2 and "limit 100 %" in s
    print("ok")
