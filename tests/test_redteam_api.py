import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from plantagent import web


class RedTeamApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.workspace = SimpleNamespace(name="sample", model_file=base / "model.json")
        patches = [mock.patch.object(web, "all_cases", side_effect=lambda kind="study": ["sample"]),
                   mock.patch.object(web, "plant", return_value=self.workspace),
                   mock.patch.dict(os.environ, {"WEB_AUTH_TOKEN": "", "WEB_ALLOW_RUNS": "0"})]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data)

    def test_replay_shape_and_missing_case_data(self):
        status, data = self.request("GET", "/api/plant/sample/redteam")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"case": "sample", "sets": []})

        raw = {"model": "muse-spark-1.3", "target": 1.2, "usd": .13, "seconds": 72, "scenarios": [
            {"name": "hot feed", "basis": "summer upset", "scale": 1.1, "pass": False,
             "changes": [{"path": "feeds.F.T_C", "value": 110}],
             "worst": {"id": "C1", "check": "flood", "utilisation": 1.18}}]}
        self.workspace.model_file.with_name("redteam_600mm.json").write_text(json.dumps(raw))
        status, data = self.request("GET", "/api/plant/sample/redteam")
        self.assertEqual(status, 200)
        attack_set = data["sets"][0]
        self.assertEqual(set(attack_set), {"id", "label", "design_label", "attacker_model", "cost_usd", "seconds",
                                           "target", "run_id", "source_url", "note", "challenge", "attacks", "summary"})
        self.assertEqual(attack_set["summary"]["broke"], 1)
        self.assertEqual(attack_set["attacks"][0]["worst"]["utilisation"], 1.18)
        status, source = self.request("GET", "/api/plant/sample/redteam?source=600-envelope")
        self.assertEqual(status, 200)
        self.assertEqual(source["scenarios"][0]["name"], "hot feed")

    def test_live_run_is_gated(self):
        status, data = self.request("POST", "/api/plant/sample/redteam/run", b"{}",
                                    {"Content-Type": "application/json"})
        self.assertEqual(status, 403)
        self.assertIn("spending actions are disabled", data["error"])
        with mock.patch.dict(os.environ, {"WEB_ALLOW_RUNS": "1"}), \
                mock.patch.object(web, "plant_job", return_value={"job": "attack"}) as job:
            status, data = self.request("POST", "/api/plant/sample/redteam/run", b"{}",
                                        {"Content-Type": "application/json"})
        self.assertEqual((status, data), (200, {"job": "attack"}))
        self.assertEqual(job.call_args.args[1].__name__, "run_featured")


if __name__ == "__main__":
    unittest.main()
