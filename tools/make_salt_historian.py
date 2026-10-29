"""Reproducible, illustrative hourly MVR salt-plant historian; no simulator or paid API.

Run: python tools/make_salt_historian.py
The patent supplies the operating point, not these instrument readings or power rating.
"""
import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "cases" / "salt_mvr" / "historian.csv"
START = datetime(2026, 8, 30)
HOURS = 60 * 24
CLEAN_START = 35 * 24
CLEAN_HOURS = 8
U_TAG = "UI-201 E-201 inferred U (W/m2K)"
FIELDS = [
    "time", "FI-1001 feed brine (t/h)", "FI-2001 P-201 circulation (m3/h)",
    "TI-2002 E-201 brine in (C)", "TI-2003 E-201 brine out (C)", "DI-201 E-201 brine rise (K)",
    "TI-201 V-201 body (C)", "PI-201 V-201 body (bar a)",
    "FI-3000 V-201 total vapour (t/h)", "FI-3001 K-201 suction (t/h)", "PI-3002 K-201 discharge (bar a)",
    "JI-201 K-201 shaft power (kW)", "TI-3003 E-201 heating steam (C)",
    "FI-5001 V-201 purge (t/h)", "FI-5101 V-301 purge disposal (t/h)",
    "FI-9001 dry salt production (t/h)", U_TAG,
]


def make_rows():
    rng = random.Random(5366514)
    impurity = 0.0
    rows = []
    for hour in range(HOURS):
        day = hour / 24
        time = (START + timedelta(hours=hour)).isoformat(timespec="minutes")
        # A one-shift water boil-out removes heater scale, not the dissolved impurity inventory.
        cleaning = CLEAN_START <= hour < CLEAN_START + CLEAN_HOURS
        age = day if day < 35 else max(0, day - 35 - CLEAN_HOURS / 24)
        u = 2450 - (850 / 35 if day < 35 else 750 / (25 - CLEAN_HOURS / 24)) * age
        purge_set = 38.1 if 18 <= day < 31 else 47.6
        impurity += ((47.6 / purge_set - 1) * 1.2 - impurity) / (10 * 24)
        bpe = 10.4 + 2.3 * impurity + 0.004 * day  # K; impurity state is an illustrative proxy
        body_p = 1.70 + 0.006 * math.sin(2 * math.pi * hour / 24)
        body_t = 125.6 + (bpe - 10.4) + 16 * (body_p - 1.70)

        # Lower U requires a larger steam/brine temperature approach to hold the same boil-up.
        required_p = 3.08 + 0.68 * (2000 / u - 1) + 0.085 * (bpe - 10.4)
        discharge_p = min(required_p, 3.20)
        load = max(0.82, 1 - 1.4 * max(0, required_p - 3.20))
        circulation = 15000 * (1 - 0.16 * (2450 - u) / 850)
        heater_dt = 2.25 * load * 15000 / circulation  # rising dT also needs lower circulation
        pressure_work = ((discharge_p / body_p) ** .23 - 1) / ((3.08 / 1.70) ** .23 - 1)
        power = 9000 * load * pressure_work  # illustrative shaft kW; patent does not state it
        feed = 362.9 * load
        suction = 226.8 * load
        salt = 94.9 * load

        def read(value, sigma):
            return round(value + rng.gauss(0, sigma), 2)

        brine_in, brine_out = read(body_t, .06), read(body_t + heater_dt, .06)
        row = dict(zip(FIELDS, [
            time, read(feed, 1.0), read(circulation, 60), brine_in,
            brine_out, round(brine_out - brine_in, 2), read(body_t, .05), read(body_p, .003),
            read(247.7 * load, .8), read(suction, .7), read(discharge_p, .005), read(power, 35),
            read(134.4 + 18 * (discharge_p - 3.08), .08),
            read(purge_set, .35), read(6.8 * purge_set / 47.6, .08),
            read(salt, .3), read(u, 8),
        ]))
        if cleaning:
            # A stopped process has zero flow/power; temperatures and pressure relax toward a water boil-out.
            for tag in FIELDS[1:]:
                row[tag] = 0 if tag.startswith(("FI-", "JI-")) else ""
        rows.append(row)
    assert len(rows) == HOURS
    assert all((START + timedelta(hours=i)).isoformat(timespec="minutes") == r["time"] for i, r in enumerate(rows))
    assert all(rows[i][U_TAG] == "" for i in range(CLEAN_START, CLEAN_START + CLEAN_HOURS))
    assert rows[CLEAN_START - 1][U_TAG] < rows[CLEAN_START + CLEAN_HOURS][U_TAG] - 500
    return rows


def main():
    rows = make_rows()
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, len(rows), "hourly samples; boil-out at day 35 (8 h)")


if __name__ == "__main__":
    main()
