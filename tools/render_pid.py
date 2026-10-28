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
svg = DrawDiagram(m.diagram, padding=5).draw_svg()
for u in set(re.findall(r'id="([0-9a-f-]{36})"', svg)) & ids.keys():
    svg = svg.replace(f'id="{u}"', f'data-pid="{ids[u][0]}" data-tag="{ids[u][1]}"')
Path(sys.argv[3]).write_text(svg)
print("wrote", sys.argv[3])
