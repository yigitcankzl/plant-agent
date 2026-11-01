"""Render a DEXPI P&ID to SVG with pyDEXPI, tagging each group with its DEXPI id and tag so the workspace can highlight it.
One-off (pyDEXPI pulls pandas/pydantic; keep it out of the runtime venv):
    <venv-with-pydexpi>/bin/python tools/render_pid.py <dir> <file.xml> <out.svg>
"""
import re
import sys
from pathlib import Path

from pydexpi.dexpi_classes.pydantic_classes import DexpiBaseModel
from pydexpi.loaders import ProteusSerializer
from pydexpi.loaders.svg_loader import DrawDiagram

m = ProteusSerializer().load(Path(sys.argv[1]), sys.argv[2])
ids, seen = {}, set()


def walk(o):
    if isinstance(o, DexpiBaseModel):
        if id(o) in seen:
            return
        seen.add(id(o))
        if getattr(o, "proteusId", None):
            ids[o.id] = (o.proteusId, getattr(o, "tagName", None) or "")
        for k in type(o).model_fields:
            walk(getattr(o, k))
    elif isinstance(o, (list, tuple)):
        for x in o:
            walk(x)


walk(m.conceptualModel)
# padding in drawing units: 5 suits millimetre sheets, but some exporters (DEXPI C02, BASF) write metres
ext = re.search(r"<Extent>\s*<Min[^>]*/>\s*<Max X=\"([0-9.]+)\" Y=\"([0-9.]+)\"", (Path(sys.argv[1]) / sys.argv[2]).read_text(errors="ignore"))
pad = min(5.0, max(float(ext.group(1)), float(ext.group(2))) * 0.02) if ext else 5
svg = DrawDiagram(m.diagram, padding=pad).draw_svg()
for u in set(re.findall(r'id="([0-9a-f-]{36})"', svg)) & ids.keys():
    svg = svg.replace(f'id="{u}"', f'data-pid="{ids[u][0]}" data-tag="{ids[u][1]}"')
if ext and pad < 5:  # metre sheet: scale to millimetres so overlays sized in mm (Rev B clouds, labels) fit the sheet
    head = re.search(r"<svg [^>]*>", svg)
    nums = [float(x) * 1000 for x in re.search(r'viewBox="([^"]+)"', head.group(0)).group(1).split()]
    box = " ".join(f"{n:g}" for n in nums)
    new = f'<svg xmlns="http://www.w3.org/2000/svg" width="{nums[2]:g}" height="{nums[3]:g}" viewBox="{box}"><g transform="scale(1000)">'
    svg = svg[:head.start()] + new + svg[head.end():].replace("</svg>", "</g></svg>")
Path(sys.argv[3]).write_text(svg)
print("wrote", sys.argv[3])
