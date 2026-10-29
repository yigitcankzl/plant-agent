"""Daily Monterey SWRO historian from Carlsbad operations and an anonymised CIP study.

Seawater temperature, salinity and the daily flow shape are the Carlsbad eSMR series.
Levels are scaled to the Monterey rated product (9.6 MGD) at the RFP maximum first-pass
recovery (45%). Membrane deviations are the Zenodo train-days, laid on a Carlsbad calendar
because that deposit has no dates. Feed pressure, channel dP and permeate conductivity are
derived (solution-diffusion screening), not measurements.

python tools/make_swro_historian.py
"""
import csv
import gzip
import json
import math
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE = ROOT / "cases" / "swro_monterey"
ESMR = Path("/home/kizil/Desktop/hackathon/case-data/raw/desal_ops/carlsbad_esmr/carlsbad_esmr_2015_2026.csv.gz")
ZENODO = Path("/home/kizil/Desktop/hackathon/case-data/raw/desal_ops/zenodo_21055948_swro_cip/extracted/data")

# RFP Appendix 2: rated product 9.6 MGD; first-pass recovery 42-45%. The historian level uses the top of that band.
PRODUCT_MGD = 9.6
RECOVERY = 0.45
START = date(2022, 1, 1)  # Zenodo day 0 is placed here; the deposit has no calendar
# Clean operating flux is below the 8.75 gfd cap. The RFP does not state the design flux.
FLUX_GFD = 8.0
# Water permeability for a 20 bar clean net driving pressure at 8 gfd. Not a membrane datasheet.
A_M_PER_S_PA = 1.8865e-12
# Salt permeability giving about 0.5% passage at the clean flux. Not a membrane datasheet.
B_M_PER_S = 2.0e-8
# 35 PSS seawater is about 27.9 bar osmotic pressure at 25 C (0.797 * 35). Screening constant, not a Pitzer model.
PI_BAR_PER_PSS_25C = 0.797
DP_CLEAN_BAR = 0.70
TRAINS = {"A": "201", "B": "202", "C": "203"}


def median(xs):
    return statistics.median(xs)


def f_to_c(f):
    return (f - 32) * 5 / 9


def gfd_to_m_s(gfd):
    return gfd * 0.003785411784 / 0.09290304 / 86400


def osmotic_bar(salinity_pss, temp_c):
    return PI_BAR_PER_PSS_25C * salinity_pss * (temp_c + 273.15) / 298.15


def log_mean_factor(recovery):
    cf = 1 / (1 - recovery)
    return (cf - 1) / math.log(cf)


def load_carlsbad():
    flow, conc, bw = defaultdict(list), defaultdict(list), defaultdict(list)
    temp, sal = [], []
    with gzip.open(ESMR, "rt") as f:
        for row in csv.DictReader(f):
            try:
                value = float(row["result"])
            except (TypeError, ValueError):
                continue
            day = date.fromisoformat(row["sampling_date"][:10])
            if row["location"] == "M-INF" and row["parameter"] == "Temperature":
                temp.append((day, f_to_c(value)))
            elif row["location"] == "M-INF" and row["parameter"] == "Salinity":
                sal.append((day, value))
            elif row["location"] == "M-001" and row["parameter"] == "Flow":
                comment = row.get("comments") or ""
                if "Reverse Osmosis Concentrate" in comment:
                    conc[day].append(value)
                elif "Backwash" in comment:
                    bw[day].append(value)
            elif row["location"] == "M-INF" and row["parameter"] == "Flow":
                flow[day].append(value)
    return ({d: median(v) for d, v in flow.items()},
            {d: median(v) for d, v in conc.items()},
            {d: median(v) for d, v in bw.items()},
            sorted(temp), sorted(sal))


def interp(samples, day):
    """Linear between weekly readings. Hold the first and last sample outside the record."""
    if day <= samples[0][0]:
        return samples[0][1]
    if day >= samples[-1][0]:
        return samples[-1][1]
    lo, hi = samples[0], samples[-1]
    for a, b in zip(samples, samples[1:]):
        if a[0] <= day <= b[0]:
            lo, hi = a, b
            break
    span = (hi[0] - lo[0]).days or 1
    return lo[1] + (hi[1] - lo[1]) * (day - lo[0]).days / span


def nearest(series, day):
    if day in series:
        return series[day], False
    earlier = [d for d in series if d < day]
    later = [d for d in series if d > day]
    if earlier and later:
        a, b = max(earlier), min(later)
        span = (b - a).days
        return series[a] + (series[b] - series[a]) * (day - a).days / span, True
    anchor = max(earlier) if earlier else min(later)
    return series[anchor], True


def load_zenodo():
    rows = defaultdict(dict)
    with open(ZENODO / "derived_daily_indicator_table.csv") as f:
        for row in csv.DictReader(f):
            rows[row["train"]][int(row["day_index"])] = row
    cip = defaultdict(list)
    with open(ZENODO / "cip_campaign_ledger.csv") as f:
        for row in csv.DictReader(f):
            cip[row["train"]].append((int(row["day_index"]), row["episode"], row["stage"]))
    return rows, cip


def fill_indicator(by_day, day, key):
    if day in by_day and by_day[day].get(key) not in ("", None):
        return float(by_day[day][key]), False
    earlier = [d for d in by_day if d < day and by_day[d].get(key) not in ("", None)]
    if not earlier:
        return 0.0, True
    return float(by_day[max(earlier)][key]), True


def days_since(cip_days, day):
    done = [d for d, _, _ in cip_days if d <= day]
    return (day - max(done)) if done else ""


def make():
    _intake, conc, bw, temp, sal = load_carlsbad()
    zenodo, cip = load_zenodo()
    days = [START + timedelta(days=i) for i in range(max(max(v) for v in zenodo.values()) + 1)]
    conc_vals = []
    filled_flow = 0
    for day in days:
        value, filled = nearest(conc, day)
        conc_vals.append(value)
        filled_flow += filled
    med_conc = median(conc_vals)
    med_bw = median([bw[d] for d in bw if START <= d <= days[-1]])
    monterey_conc = PRODUCT_MGD * (1 - RECOVERY) / RECOVERY
    scale = monterey_conc / med_conc
    bw_ratio = med_bw / med_conc
    lm = log_mean_factor(RECOVERY)
    j_clean = gfd_to_m_s(FLUX_GFD)
    ndp_clean_bar = (j_clean / A_M_PER_S_PA) / 1e5
    fields = ["time", "FI-1001 seawater feed (MGD)", "FI-2001 first-pass concentrate (MGD)",
              "FI-1002 media backwash (MGD)", "TI-1001 seawater temperature (C)", "SI-1001 seawater salinity (PSS)"]
    for n in TRAINS.values():
        fields += [f"QI-{n} net driving pressure deviation (fraction)", f"QI-{n} differential pressure deviation (fraction)",
                   f"QI-{n} specific flux deviation (fraction)", f"QI-{n} salt passage deviation (fraction)",
                   f"PI-{n} first-pass feed (bar)", f"CI-{n} first-pass permeate (uS/cm)",
                   f"DPI-{n} feed-channel dP (bar)", f"XI-{n} days since CIP (d)"]
    out_rows = []
    carried = 0
    for i, day in enumerate(days):
        t_c = interp(temp, day)
        s_pss = interp(sal, day)
        conc_m = conc_vals[i] * scale
        feed_m = conc_m / (1 - RECOVERY)
        bw_day, bw_filled = nearest(bw, day)
        row = {"time": datetime(day.year, day.month, day.day).isoformat(timespec="minutes"),
               "FI-1001 seawater feed (MGD)": round(feed_m, 3),
               "FI-2001 first-pass concentrate (MGD)": round(conc_m, 3),
               "FI-1002 media backwash (MGD)": round(bw_day * scale, 3),
               "TI-1001 seawater temperature (C)": round(t_c, 2),
               "SI-1001 seawater salinity (PSS)": round(s_pss, 2)}
        pi_lm = osmotic_bar(s_pss, t_c) * lm
        tds = s_pss * 1000  # PSS taken as g/m3 for the derived conductivity only
        for src, n in TRAINS.items():
            ndp, c1 = fill_indicator(zenodo[src], i, "ndp_pct")
            dp, c2 = fill_indicator(zenodo[src], i, "dp_pct")
            flux, c3 = fill_indicator(zenodo[src], i, "flux_pct")
            sp, c4 = fill_indicator(zenodo[src], i, "sp_pct")
            carried += c1 or c2 or c3 or c4
            # Hold the day's throughput. The deposited NDP deviation raises the pressure required to do that.
            p_feed = ndp_clean_bar * (1 + ndp) + pi_lm + 1.0
            passage = (B_M_PER_S / (j_clean + B_M_PER_S)) * (1 + sp)
            row[f"QI-{n} net driving pressure deviation (fraction)"] = round(ndp, 4)
            row[f"QI-{n} differential pressure deviation (fraction)"] = round(dp, 4)
            row[f"QI-{n} specific flux deviation (fraction)"] = round(flux, 4)
            row[f"QI-{n} salt passage deviation (fraction)"] = round(sp, 4)
            row[f"PI-{n} first-pass feed (bar)"] = round(p_feed, 2)
            row[f"CI-{n} first-pass permeate (uS/cm)"] = round(tds * passage * 2.0, 1)
            row[f"DPI-{n} feed-channel dP (bar)"] = round(DP_CLEAN_BAR * (1 + dp), 3)
            since = days_since(cip[src], i)
            row[f"XI-{n} days since CIP (d)"] = since
        if bw_filled:
            filled_flow += 0  # counted separately below
        out_rows.append(row)
    CASE.mkdir(parents=True, exist_ok=True)
    with open(CASE / "historian.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    cold = min(out_rows, key=lambda r: (r["TI-1001 seawater temperature (C)"], -r["SI-1001 seawater salinity (PSS)"]))
    salty = max(out_rows, key=lambda r: r["SI-1001 seawater salinity (PSS)"])
    meta = {
        "rows": len(out_rows),
        "start": out_rows[0]["time"],
        "end": out_rows[-1]["time"],
        "carlsbad_concentrate_median_mgd": round(med_conc, 2),
        "carlsbad_backwash_median_mgd": round(med_bw, 3),
        "scale_on_concentrate": round(scale, 4),
        "monterey_feed_median_mgd": round(median([r["FI-1001 seawater feed (MGD)"] for r in out_rows]), 2),
        "monterey_concentrate_median_mgd": round(median([r["FI-2001 first-pass concentrate (MGD)"] for r in out_rows]), 2),
        "flow_days_interpolated": filled_flow,
        "temperature_min_C": min(r["TI-1001 seawater temperature (C)"] for r in out_rows),
        "temperature_max_C": max(r["TI-1001 seawater temperature (C)"] for r in out_rows),
        "salinity_min": min(r["SI-1001 seawater salinity (PSS)"] for r in out_rows),
        "salinity_max": max(r["SI-1001 seawater salinity (PSS)"] for r in out_rows),
        "cold_day": {"time": cold["time"], "T_C": cold["TI-1001 seawater temperature (C)"],
                     "PSS": cold["SI-1001 seawater salinity (PSS)"], "P_bar": cold["PI-201 first-pass feed (bar)"]},
        "salty_day": {"time": salty["time"], "T_C": salty["TI-1001 seawater temperature (C)"],
                      "PSS": salty["SI-1001 seawater salinity (PSS)"], "P_bar": salty["PI-201 first-pass feed (bar)"]},
        "ndp_clean_bar": round(ndp_clean_bar, 2),
        "log_mean_concentration_factor": round(lm, 3),
        "bw_ratio": round(bw_ratio, 4),
    }
    (CASE / "historian_map.json").write_text(json.dumps({
        "file": "historian.csv",
        "note": "Carlsbad eSMR temperature, salinity and daily RO-concentrate shape, scaled to Monterey 9.6 MGD at 45% recovery. "
                "Zenodo CC-BY-4.0 train deviations (trains A/B/C on RO-201/202/203) supply fouling and CIP timing. "
                "PI, DPI and CI columns are solution-diffusion estimates, not transmitters. See historian_basis.md.",
        "target_scale": 12.8 / 9.6,
        "limits": [
            {"tag": "PI-201 first-pass feed (bar)", "name": "RO-201 feed pressure vs 1000 psi", "max": 68.95, "warn_margin": 3},
            {"tag": "PI-202 first-pass feed (bar)", "name": "RO-202 feed pressure vs 1000 psi", "max": 68.95, "warn_margin": 3},
            {"tag": "PI-203 first-pass feed (bar)", "name": "RO-203 feed pressure vs 1000 psi", "max": 68.95, "warn_margin": 3},
        ],
    }, indent=1) + "\n")
    (CASE / "historian_basis.md").write_text(basis_text(meta))
    print(json.dumps(meta, indent=1))


def basis_text(meta):
    return f"""# Monterey SWRO historian: sources and transformations

`historian.csv` has {meta['rows']} daily rows, {meta['start'][:10]} through {meta['end'][:10]}.
It is not a Monterey plant export. Monterey had no operating plant when the 2013 RFP was issued.
Three labelled pieces are combined. Pressures and permeate conductivities are calculated.

## 1. Carlsbad flow, temperature and salinity

Source: California State Water Resources Control Board CIWQS eSMR, facility place id 640063,
Claude "Bud" Lewis Carlsbad Desalination Plant, NPDES CA0109223. File
`case-data/raw/desal_ops/carlsbad_esmr/carlsbad_esmr_2015_2026.csv.gz`. License: public domain
(`other-pd` on data.ca.gov). See that folder's SOURCE.txt.

Columns used:

- `M-001` Flow whose comment is `Continuous Reading; Reverse Osmosis Concentrate`, daily, MGD.
  In this window the median is {meta['carlsbad_concentrate_median_mgd']} MGD.
- `M-001` Flow whose comment is `Calculated Flows of Media Filtration Backwash`. Median
  {meta['carlsbad_backwash_median_mgd']} MGD.
- `M-INF` Temperature, degrees F, about weekly, converted with (F − 32) × 5/9.
- `M-INF` Salinity, ppth, PSS-78, about weekly. Used as PSS.

Not used as Monterey intake: `M-INF` Flow (`Total Source Water Flow (CDP Intake)`). That series
includes dilution water for the Encina co-discharge and is several times the RO feed. Monterey's
slant-well intake has no such dilution stream.

Scaling. The RFP caps first-pass recovery at 45% (RFP PDF p.346). Rated product is 9.6 MGD
(RFP PDF p.332). Design concentrate at that corner is 9.6 × (1 − 0.45) / 0.45 = {meta['monterey_concentrate_median_mgd']} MGD
on the median day. Each Carlsbad concentrate day is multiplied by {meta['scale_on_concentrate']}.
Feed is that concentrate divided by (1 − 0.45), so the recovery in the file is exactly 45% and the
median feed is {meta['monterey_feed_median_mgd']} MGD. Backwash is the Carlsbad backwash day times the
same concentrate scale factor. The shape is Carlsbad's; the level is Monterey's.

Days with no concentrate or backwash sample are linearly filled from the neighbouring samples
({meta['flow_days_interpolated']} concentrate days in this window were filled). Weekly temperature and
salinity are linearly interpolated and held flat outside the first and last sample. This window's
temperature is {meta['temperature_min_C']} to {meta['temperature_max_C']} C and salinity is
{meta['salinity_min']} to {meta['salinity_max']} PSS. Carlsbad does not reach Monterey's 8 C design
minimum (RFP PDF p.428). The coldest day in this file is {meta['cold_day']['time'][:10]} at
{meta['cold_day']['T_C']} C and {meta['cold_day']['PSS']} PSS. The saltiest day is
{meta['salty_day']['time'][:10]} at {meta['salty_day']['PSS']} PSS. Those are Carlsbad observations,
not the RFP design corner (8 C and 37 PSS together).

## 2. Anonymised SWRO fouling and CIP

Source: Su, Yi Hsiang, Zenodo record 21055948, version 1.3 (2026-06-30), CC-BY-4.0.
`derived_daily_indicator_table.csv` and `cip_campaign_ledger.csv`. The plant, the membrane model,
the area and the calendar were removed by the author. `ndp_pct` is the fractional deviation of net
driving pressure from a fixed commissioning baseline, `dp_pct` the normalised feed-channel
differential pressure, `flux_pct` the 25 C specific flux, and `sp_pct` the 25 C salt passage.
Deviations are one-sided and clipped to the range 0 to 1. There are 18 CIP episodes.

Trains A, B and C are applied to Monterey tags RO-201, RO-202 and RO-203. The RFP module is 1.6 MGD
and the 9.6 MGD rated plant implies more than three trains (see basis.md). Only three trains carry
this fouling record. Zenodo `day_index` 0 is placed on {meta['start'][:10]}. That alignment is a
label, not the withheld plant's calendar. A missing train-day copies the previous deviation.

`XI-201`, `XI-202` and `XI-203` are days since that train's last CIP on this labelled calendar.
They are blank before the first CIP.

## 3. Derived pressure and conductivity

These columns are not in either dataset. They use a solution-diffusion screening so a limit check
has a pressure to read. Constants that are not in the RFP or the SCADA:

- Operating flux {FLUX_GFD} gfd, below the RFP maximum of 8.75 gfd. The RFP does not state the design flux.
- Water permeability A = {A_M_PER_S_PA} m/(s·Pa). Clean net driving pressure is {meta['ndp_clean_bar']} bar.
- Salt permeability B = {B_M_PER_S} m/s.
- Osmotic pressure (bar) = {PI_BAR_PER_PSS_25C} × salinity (PSS) × T(K) / 298.15, because 35 PSS is taken as 27.9 bar at 25 C.
- With nearly complete rejection, the concentrate factor is 1/(1 − 0.45) and the log-mean factor along the vessel is {meta['log_mean_concentration_factor']}.
- Feed pressure (bar) = clean NDP × (1 + ndp deviation) + log-mean osmotic pressure + 1 bar permeate backpressure.
  Throughput is not cut when the flux deviation rises; the NDP deviation is what raises pressure. The flux deviation is still stored.
- Channel dP (bar) = {DP_CLEAN_BAR} × (1 + dp deviation). The 0.70 bar clean value is not a measurement.
- Permeate TDS ≈ (salinity × 1000) × (B / (J + B)) × (1 + salt-passage deviation), with PSS used as g/m³.
  Conductivity (µS/cm) ≈ 2 × that TDS. This is a first-pass screening result, not finished water, and it ignores the partial second pass.

On the cold day above, the derived RO-201 feed pressure is {meta['cold_day']['P_bar']} bar. On the salty day it is {meta['salty_day']['P_bar']} bar.
The RFP feed-pressure ceiling is 1000 psi (68.95 bar) (RFP PDF p.346).
"""


if __name__ == "__main__":
    make()
