"""Data sheet reading (Muse vision stubbed): unit conversion, plausibility refusals, and the confirm path into the inputs."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import assumptions, datasheet


def q(value, unit, page=1, label="x"):
    return {"value": value, "unit": unit, "page": page, "label": label}


def reading(**over):
    """The OSU vendor sheet as Muse should read it: 500 USgpm at 435 ft, 79.98 %, 69.02 hp shaft, MCSF 348.2 USgpm."""
    raw = {"equipment": "pump", "model": "475SR60F86-0786", "tag": "",
           "rated": {"flow": q(500, "USgpm", label="Flow, rated"), "head": q(435, "ft", label="Head, rated"),
                     "efficiency": q(79.98, "%"), "shaft_power": q(69.02, "hp", label="Power, rated"),
                     "motor_power": q(75, "hp", label="75 HP"), "speed": q(3450, "rpm"), "min_flow": q(348.2, "USgpm", label="MCSF"),
                     "shutoff_head": q(726.6, "ft", label="Head max."), "voltage": q(None, "")},
           "curve": [{"flow": 0, "head": 726, "efficiency_pct": None}, {"flow": 200, "head": 650, "efficiency_pct": 55},
                     {"flow": 400, "head": 520, "efficiency_pct": 77}, {"flow": 500, "head": 437, "efficiency_pct": 80},
                     {"flow": 600, "head": 330, "efficiency_pct": 76}],
           "curve_units": {"flow": "USgpm", "head": "ft", "page": 2}, "unreadable": []}
    raw.update(over)
    return raw


class DatasheetTest(unittest.TestCase):
    def test_units_and_checks_pass(self):
        r = datasheet.normalise(reading())
        self.assertTrue(r["ok"], r["refused"])
        self.assertAlmostEqual(r["rated"]["flow_m3h"], 113.56, places=1)
        self.assertAlmostEqual(r["rated"]["head_m"], 132.59, places=1)
        self.assertAlmostEqual(r["rated"]["shaft_kw"], 51.47, places=1)
        self.assertEqual(r["rated"]["efficiency"], 0.7998)
        self.assertEqual(r["where"]["min_flow_m3h"]["label"], "MCSF")

    def test_rising_head_is_refused(self):
        bad = reading(curve=[{"flow": 0, "head": 300, "efficiency_pct": None}, {"flow": 300, "head": 500, "efficiency_pct": None},
                             {"flow": 600, "head": 700, "efficiency_pct": None}])
        r = datasheet.normalise(bad)
        self.assertFalse(r["ok"])
        self.assertIn("fall", r["refused"])

    def test_power_mismatch_is_refused(self):
        raw = reading()
        raw["rated"]["shaft_power"] = q(20, "hp")  # a misread: 15 kW against ~51 kW from rho g Q H / eta
        self.assertIn("shaft power", datasheet.normalise(raw)["refused"])

    def test_efficiency_out_of_range_is_refused(self):
        raw = reading()
        raw["rated"]["efficiency"] = q(180, "%")
        self.assertFalse(datasheet.normalise(raw)["ok"])

    def test_confirm_applies_curve_and_motor_with_source(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            with mock.patch.object(assumptions, "ws_dir", lambda case: tmp / case), \
                    mock.patch.object(datasheet.llm, "complete", return_value={"content": json.dumps(reading())}), \
                    mock.patch.object(datasheet.llm, "set_tag"), \
                    mock.patch("plantagent.drafts.resolve_uploads", return_value={}):
                up = assumptions.upload("demo", "datasheet", b"\x89PNG\r\n\x1a\n" + _png(), "osu sheet.png", read=True)
                self.assertTrue(up["reading"]["ok"])
                with self.assertRaises(ValueError):
                    assumptions.apply_datasheet("demo", up["name"], "")  # a tag is required
                out = assumptions.apply_datasheet("demo", up["name"], "P-301", user="tester")
            curves = json.loads((tmp / "demo" / "inputs" / "curves.json").read_text())
            motors = json.loads((tmp / "demo" / "inputs" / "motors.json").read_text())
            pts = curves["curves"][0]["points"]
            self.assertEqual(curves["curves"][0]["id"], "P-301")
            self.assertAlmostEqual(pts[0]["flow_m3h"], 79.08, places=1)  # starts at the vendor's MCSF, the minimum-flow row
            self.assertIn("page(s) 1, 2", curves["note"])
            self.assertIn("confirmed by tester", curves["note"])
            self.assertAlmostEqual(motors["motors"][0]["kw"], 55.93, places=1)  # the 75 hp motor rating
            self.assertEqual(set(out["applied"]), {"curves", "motors"})
        finally:
            shutil.rmtree(tmp)

    def test_axis_title_units_and_prose_tag(self):
        # what Muse Spark Open really returned for the OSU sheet: whole axis titles as units, prose in the tag field
        raw = reading(tag="not on sheet -> value null",
                      curve_units={"flow": "USgpm | Head - ft | Efficiency - %", "head": "ft | Flow - USgpm | Power - hp", "page": 2})
        r = datasheet.normalise(raw)
        self.assertTrue(r["ok"], r["refused"])
        self.assertEqual(r["tag"], "")
        self.assertAlmostEqual(r["curve"][3]["flow_m3h"], 113.56, places=1)
        self.assertAlmostEqual(r["curve"][3]["head_m"], 133.2, places=1)
        self.assertIsNone(datasheet._unit(datasheet._HEAD, "mm"))  # 'm' must not match inside 'mm'
        self.assertEqual(datasheet.normalise(reading(tag="P-4711"))["tag"], "P-4711")

    def test_non_sheet_upload_is_refused(self):
        with self.assertRaises(ValueError):
            assumptions.upload("demo", "datasheet", b"hello", "x.txt")


def _png():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    return buf.getvalue()[8:]


if __name__ == "__main__":
    unittest.main()
