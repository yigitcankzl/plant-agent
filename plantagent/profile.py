"""Gravity hydraulic profile of a treatment train (US units: mgd, ft, in).

The spec lists the structures from the downstream control (clearwell) upstream. Each element turns the water surface
below it into the water surface above it at a given flow, the way an engineer computes a hydraulic profile by hand.
The agent builds the spec from the documents; this module does the arithmetic.
"""
import math

G = 32.174
CFS_PER_MGD = 1.5472

SPEC_HELP = {
    "start": "{id, ws_ft} downstream control water surface (e.g. clearwell high water)",
    "elements": "list, downstream -> upstream. Put drawing_ws_ft on any element whose water surface is labelled on the "
                "drawing (used for calibration residuals and to place results on the sheet). Each {type, id, ...}; optional limits: max_ws_ft (spill/overtop level) "
                "with limit_name, min_ws_ft, max_flow_mgd (a capacity or rating stated by the document, per unit) with rating_name. `share` = fraction of plant flow through this element (default 1; e.g. 0.25 "
                "for one of four filters, 0.5 for one of two parallel basins).",
    "types": {
        "control": "{ws_ft, required_drop_ft?}: level held by a valve (filter level). Checks ws_ft - downstream >= required_drop_ft.",
        "pipe": "{length_ft, diameter_in, c_factor=120, minor_k=0} or calibrate:{flow_mgd, headloss_ft} (fits the loss "
                "coefficient to a field test; share applies to the test flow too). Loss = Hazen-Williams + minor_k*V2/2g.",
        "weir": "{kind: rectangular|vnotch, crest_ft, length_ft (rectangular) | notches + angle_deg=90 (vnotch), cd?} "
                "or calibrate:{flow_mgd, head_ft}. Free fall unless the downstream water surface rises above the crest "
                "(then submerged, Villemonte).",
        "orifice": "{area_ft2, cd=0.6}: gate or port, loss = (Q/(cd A))^2/2g.",
        "drop": "{loss_ft}: a fixed loss given by the document at `at_flow_mgd`, scaled with Q^2.",
    },
}


def _hw_loss(q_cfs, length_ft, d_in, c):
    d = d_in / 12
    return 4.73 * length_ft * q_cfs ** 1.852 / (c ** 1.852 * d ** 4.87)


def _weir_q(e, h):
    """Free-flow weir discharge, cfs, for head h (ft) over the crest."""
    if h <= 0:
        return 0.0
    if e.get("kind", "rectangular") == "vnotch":
        cd = e.get("cd", 0.58)
        return e["notches"] * cd * 8 / 15 * math.sqrt(2 * G) * math.tan(math.radians(e.get("angle_deg", 90)) / 2) * h ** 2.5
    return e.get("cd", 3.33) * e["length_ft"] * h ** 1.5


def _weir_head(e, q, h_down):
    """Upstream head over the crest passing q with downstream head h_down (Villemonte submergence)."""
    n = 2.5 if e.get("kind") == "vnotch" else 1.5
    lo, hi = max(h_down, 0.0), max(h_down, 0.0) + 50
    for _ in range(100):
        h = (lo + hi) / 2
        qh = _weir_q(e, h) * (1 - (max(h_down, 0) / h) ** n) ** 0.385 if h > 0 else 0
        lo, hi = (h, hi) if qh < q else (lo, h)
    return (lo + hi) / 2


def _calibrated(e, flow_mgd):
    """Fit a pipe's or weir's coefficient to a measured point; returns a copy with the fitted value and its basis."""
    c = e.get("calibrate")
    if not c:
        return dict(e)
    e = dict(e)
    q = c["flow_mgd"] * e.get("share", 1) * CFS_PER_MGD
    if e["type"] == "pipe":
        e["k_fit"] = c["headloss_ft"] / q ** 1.852  # h = k Q^1.852
        if "diameter_in" in e and "length_ft" in e:
            e["implied_c_factor"] = round((4.73 * e["length_ft"] * q ** 1.852 / (c["headloss_ft"] * (e["diameter_in"] / 12) ** 4.87)) ** (1 / 1.852))
    elif e["type"] == "weir":
        h = c["head_ft"]
        base = _weir_q({**e, "cd": 1.0}, h)  # discharge with unit coefficient
        e["cd"] = q / base
    return e


def run(spec, flow_mgd):
    """Water surface at every structure for one plant flow. Returns nodes upstream-last, with margins to limits."""
    ws = spec["start"]["ws_ft"]
    nodes = [{"id": spec["start"]["id"], "ws_ft": round(ws, 2), "loss_ft": 0.0}]
    checks = []
    for raw in spec["elements"]:
        e = _calibrated(raw, flow_mgd)
        q = flow_mgd * e.get("share", 1) * CFS_PER_MGD
        t, note = e["type"], ""
        if t == "control":
            drop = e["ws_ft"] - ws
            if "required_drop_ft" in e:
                checks.append({"id": e["id"], "check": "driving head", "available_ft": round(drop, 2),
                               "required_ft": e["required_drop_ft"], "margin_ft": round(drop - e["required_drop_ft"], 2),
                               "margin": round(drop - e["required_drop_ft"], 2), "unit": "ft", "scale": e["required_drop_ft"]})
            up = e["ws_ft"]
        elif t == "pipe":
            if "k_fit" in e:
                loss = e["k_fit"] * q ** 1.852
            else:
                loss = _hw_loss(q, e["length_ft"], e["diameter_in"], e.get("c_factor", 120))
            area = math.pi / 4 * (e["diameter_in"] / 12) ** 2 if "diameter_in" in e else None
            v = q / area if area else None
            if v is not None and "k_fit" not in e:  # a field calibration already contains the fitting losses
                loss += e.get("minor_k", 0) * v * v / (2 * G)
                note = f"V={v:.2f} fps"
            up = ws + loss
        elif t == "weir":
            crest = e["crest_ft"]
            up = crest + _weir_head(e, q, ws - crest)
            note = "submerged" if ws > crest else "free fall"
        elif t == "orifice":
            up = ws + (q / (e.get("cd", 0.6) * e["area_ft2"])) ** 2 / (2 * G)
        elif t == "drop":
            up = ws + e["loss_ft"] * (flow_mgd / e["at_flow_mgd"]) ** 2
        else:
            raise ValueError(f"unknown element type {t!r}; use one of {list(SPEC_HELP['types'])}")
        node = {"id": e["id"], "ws_ft": round(up, 2), "loss_ft": round(up - ws, 3)}
        if note:
            node["note"] = note
        for k in ("implied_c_factor",):
            if k in e:
                node[k] = e[k]
        if "cd" in e and t == "weir" and raw.get("calibrate"):
            node["fitted_cd"] = round(e["cd"], 3)
        if "max_ws_ft" in e:
            checks.append({"id": e["id"], "check": e.get("limit_name", "max water surface"), "ws_ft": round(up, 2),
                           "limit_ft": e["max_ws_ft"], "margin_ft": round(e["max_ws_ft"] - up, 2),
                           "margin": round(e["max_ws_ft"] - up, 2), "unit": "ft", "scale": max(abs(up - ws), 0.5)})
        if "min_ws_ft" in e:
            checks.append({"id": e["id"], "check": e.get("limit_name", "min water surface"), "ws_ft": round(up, 2),
                           "limit_ft": e["min_ws_ft"], "margin_ft": round(up - e["min_ws_ft"], 2),
                           "margin": round(up - e["min_ws_ft"], 2), "unit": "ft", "scale": max(abs(up - ws), 0.5)})
        if "drawing_ws_ft" in e:
            node["drawing_ws_ft"] = e["drawing_ws_ft"]
            node["residual_ft"] = round(up - e["drawing_ws_ft"], 2)
        if "max_flow_mgd" in e:
            per_unit = flow_mgd * e.get("share", 1)
            checks.append({"id": e["id"], "check": e.get("rating_name", "stated capacity"), "flow_mgd": round(per_unit, 2),
                           "limit_mgd": e["max_flow_mgd"], "margin_mgd": round(e["max_flow_mgd"] - per_unit, 2),
                           "margin": round(e["max_flow_mgd"] - per_unit, 2), "unit": "mgd", "scale": e["max_flow_mgd"]})
        nodes.append(node)
        ws = up
    failing = [c for c in checks if c["margin"] < 0]
    return {"flow_mgd": flow_mgd, "nodes": nodes, "checks": checks, "passes": not failing,
            # margins are in ft (levels) or mgd (ratings): compare them relative to their own scale
            "first_limit": min(checks, key=lambda c: c["margin"] / (c["scale"] or 1))["id"] if checks else None}


def capacity(spec, lo=0.5, hi=60.0):
    """Flow at which each check reaches zero margin (bisection per check). None = still passes at hi."""
    ids = [(c["id"], c["check"]) for c in run(spec, lo)["checks"]]
    out = []
    for cid, name in ids:
        margin = lambda q: next(c["margin"] for c in run(spec, q)["checks"] if (c["id"], c["check"]) == (cid, name))  # noqa: E731
        if margin(lo) < 0:
            out.append({"id": cid, "check": name, "binds_at_mgd": f"< {lo}"}); continue
        if margin(hi) >= 0:
            out.append({"id": cid, "check": name, "binds_at_mgd": None}); continue
        a, b = lo, hi
        for _ in range(40):
            m = (a + b) / 2
            a, b = (m, b) if margin(m) >= 0 else (a, m)
        out.append({"id": cid, "check": name, "binds_at_mgd": round(a, 2)})
    return sorted(out, key=lambda r: float("inf") if r["binds_at_mgd"] is None else -1 if isinstance(r["binds_at_mgd"], str) else r["binds_at_mgd"])


if __name__ == "__main__":
    # Rectangular weir: 9 ft at 1 ft head ~ 30 cfs ~ 19 mgd (Roseburg p.114 states 19 mgd).
    assert abs(_weir_q({"length_ft": 9}, 1.0) / CFS_PER_MGD - 19.4) < 0.3
    # 30-inch pipe, 100 ft at 18 mgd: Roseburg Table 4-1 gives 0.25 ft/100 ft, i.e. C ~150 (new lined steel).
    assert abs(_hw_loss(18 * CFS_PER_MGD, 100, 29.5, 150) - 0.25) < 0.05
    spec = {"start": {"id": "filter", "ws_ft": 464.0}, "elements": [
        {"type": "pipe", "id": "settled pipe", "diameter_in": 42, "length_ft": 300, "calibrate": {"flow_mgd": 13.1, "headloss_ft": 2.8 / 12}},
        {"type": "drop", "id": "channel", "loss_ft": 0.0, "at_flow_mgd": 1, "max_ws_ft": 465.0, "limit_name": "overflow weir"},
        {"type": "weir", "id": "launders", "kind": "vnotch", "crest_ft": 465.83, "notches": 400}]}
    r = run(spec, 13.1)
    assert abs(r["nodes"][1]["ws_ft"] - (464.0 + 2.8 / 12)) < 0.01, r
    assert r["nodes"][3]["note"] == "free fall"
    cap = capacity(spec)
    assert 28 < cap[0]["binds_at_mgd"] < 30, cap  # 0.233 ft at 13.1 mgd reaches 1.0 ft at 13.1 * 4.29^(1/1.852)
    print("ok", r["nodes"], cap)
