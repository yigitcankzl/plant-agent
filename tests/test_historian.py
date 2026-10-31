"""Historian connector: CSV export and a PI Web API compatible server (local mock, no network) feed the same rows,
mapped model inputs and the fouling-forecast fit."""
import json
import os
import threading
import unittest
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from plantagent import forecast, historian

T0 = datetime(2026, 10, 1)
SERIES = {  # webId -> recorded values: U falls 20 W/m2K per day; one bad-quality value and one digital state are skipped
    "W-U": [{"Timestamp": (T0 + timedelta(hours=h)).isoformat() + "Z", "Value": 2400 - 20 * h / 24, "Good": True} for h in range(0, 24 * 10, 2)]
    + [{"Timestamp": (T0 + timedelta(hours=5)).isoformat() + "Z", "Value": 99999, "Good": False}],
    "W-F": [{"Timestamp": (T0 + timedelta(hours=h, minutes=30)).isoformat() + "Z", "Value": 360.0, "Good": True} for h in range(24 * 10)]
    + [{"Timestamp": (T0 + timedelta(hours=7)).isoformat() + "Z", "Value": {"Name": "Shutdown", "Value": 248}, "Good": True}],
}


class PI(BaseHTTPRequestHandler):
    def do_GET(self):  # /piwebapi/streams/{webId}/recorded?startTime=...
        parts = self.path.split("?")[0].strip("/").split("/")
        ok = parts[:2] == ["piwebapi", "streams"] and parts[3] == "recorded" and self.headers.get("Authorization") == "Bearer t0ken"
        body = json.dumps({"Items": SERIES.get(parts[2], [])} if ok else {"Errors": ["no"]}).encode()
        self.send_response(200 if ok else 401)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TestHistorian(unittest.TestCase):
    def test_pi_web_api_rows_feed_model_inputs_and_forecast(self):
        srv = HTTPServer(("127.0.0.1", 0), PI)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        cfg = {"pi": {"web_ids": {"UI-201 U": "W-U", "FI-1001 feed": "W-F"}, "start": "*-10d"},
               "model_inputs": [{"tag": "FI-1001 feed", "path": "feeds.F.kg_h", "factor": 1000, "window_h": 24}]}
        env = {"PI_WEB_API_URL": f"http://127.0.0.1:{srv.server_port}/piwebapi", "PI_WEB_API_TOKEN": "t0ken"}
        try:
            with mock.patch.dict(os.environ, env):
                self.assertEqual(historian.source(cfg), "pi")
                rs = historian.rows("any_case", cfg)
        finally:
            srv.shutdown()
            srv.server_close()
        self.assertEqual(len(rs), 240)  # hourly rows over 10 days
        self.assertTrue(all(r["UI-201 U"] is None or r["UI-201 U"] < 3000 for r in rs))  # the bad-quality 99999 is skipped
        self.assertTrue(all(r["FI-1001 feed"] == 360.0 for r in rs))  # the digital state is skipped
        self.assertEqual(historian.model_inputs(rs, cfg["model_inputs"])[0]["value"], 360000.0)
        f = forecast.fit(forecast.daily_u(rs, "UI-201 U"))  # the same rows feed the fouling forecast
        self.assertAlmostEqual(f["slope_per_day"], -20, delta=0.5)

    def test_csv_export_rows_and_model_inputs(self):
        with mock.patch.dict(os.environ, {"PI_WEB_API_URL": ""}):
            s = historian.summary("salt_mvr")
        self.assertEqual(s["source"], "csv")
        self.assertGreater(s["n_rows"], 1000)
        feed = next(m for m in s["model_inputs"] if m["path"] == "feeds.S1004mix.kg_h")
        self.assertTrue(300000 < feed["value"] < 420000)  # FI-1001 t/h x 1000 near the 362.9 t/h Table I feed


if __name__ == "__main__":
    unittest.main()
