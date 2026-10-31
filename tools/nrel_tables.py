"""Extract the Appendix E stream tables of NREL/TP-5100-47764 (Humbird et al. 2011) into JSON.
python tools/nrel_tables.py <47764.pdf> <out.json>
Each PFD page carries a table: a COMPONENT header row with stream numbers, then one row per property/component;
values are right-aligned under the stream numbers, so a value belongs to the header token whose right edge it shares."""
import json
import re
import subprocess
import sys

FIRST, LAST = 125, 146  # PDF pages of the Appendix E stream tables


def page_text(pdf, page):
    return subprocess.run(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"],
                          capture_output=True, text=True, check=True).stdout


def parse_page(text, page, out):
    hdr = None
    for m in re.finditer(r"\b([QW][A-Z]{1,2}\d{3}[A-Z]?)\s+(-?[\d,]+\.?\d*)(?:\s+(-?[\d.]+))?", text):
        # heat streams: Gcal/hr; work streams: kW (then Gcal/hr)
        key, v = m.group(1), float(m.group(2).replace(",", ""))
        out.setdefault("_energy", {})[key] = {"page": page, **({"Gcal_h": v} if key[0] == "Q" else {"kW": v})}
    for ln in text.split("\n"):
        side = re.search(r"\s{3}(Heat Stream|Work Stream|Q[A-Z]{1,2}\d|W[A-Z]{1,2}\d)", ln)
        body = ln[:side.start()] if side else ln
        if body.startswith("COMPONENT"):
            hdr = [(m.group(), m.end()) for m in re.finditer(r"\S+", body)][2:]
            for t, _ in hdr:
                out.setdefault(t, {"page": page})
            continue
        name = re.match(r"^(\S.*?)(?=\s{2,})", body)
        if not hdr or not name:
            continue
        nm = name.group(1).strip()
        for v in re.finditer(r"-?[\d,]+\.?\d*%?", body):
            if v.start() < 40:
                continue
            best = min(hdr, key=lambda h: abs(h[1] - v.end()))
            if abs(best[1] - v.end()) <= 4:
                s = v.group().replace(",", "")
                out[best[0]][nm] = float(s.rstrip("%")) / (100 if s.endswith("%") else 1)


def main(pdf, dest):
    out = {}
    for p in range(FIRST, LAST + 1):
        parse_page(page_text(pdf, p), p, out)
    json.dump(out, open(dest, "w"), indent=1)
    print(len(out), "streams")


if __name__ == "__main__":
    main(*sys.argv[1:3])
