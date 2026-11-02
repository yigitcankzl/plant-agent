import base64
import copy
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from PIL import Image

from plantagent import audit, redline, web
from plantagent.plant import PlantWorkspace


def png():
    out = io.BytesIO()
    Image.new("RGB", (120, 80), "white").save(out, "PNG")
    return out.getvalue()


class RedlineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        patch = mock.patch.object(audit, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.w = object.__new__(PlantWorkspace)
        self.w.name, self.w.model = "salt_mvr", "muse-wonder-1.0"
        self.w.model_file = self.root / "ws" / "salt_mvr" / "model.json"
        self.w.dir = self.w.model_file.parent / "session"
        self.w.cfg = {"target_scale": 1.2, "engine": "dwsim", "svg": "pid.svg"}
        self.w.built = {"label": "fake salt model", "spec": {
            "compounds": ["Water"], "feeds": {"FEED": {"kg_h": 100, "x": {"Water": 1}}},
            "units": [{"id": "V-201", "type": "evaporator", "in": "FEED", "out": "BRINE", "U_W_m2K": 2000},
                      {"id": "P-101", "type": "pump", "in": "BRINE", "out": "PRODUCT"}],
            "limits": {"P-101": {"max_m3_h": 100}},
        }}
        self.w.pid = {"equipment": [{"tag": "E-201"}, {"tag": "V-201"}, {"tag": "P-101"}]}
        self.w.answers = [{"headline": "Muse's saved design", "proposals": [{"verified": True,
                          "changes": [{"path": "units.V-201.U_W_m2K", "value": 2400}]}]}]
        self.w.revisions, self.w.runs, self.w._state = [], {}, {}
        self.raw = {"items": [
            {"ink": "E-201 clean to U 2,500", "tag": "E-201", "confidence": 0.95,
             "change": {"path": "units.V-201.U_W_m2K", "value": 2500,
                        "physical_change": "clean heater", "rating_source": "red ink U 2,500; engineer to confirm"}, "unreadable": []},
            {"ink": "add parallel pump P-101B", "tag": "P-101", "confidence": 0.8,
             "change": {"add_unit": {"id": "P-101B", "type": "pump", "in": "BRINE", "out": "BRINE2"}},
             "unreadable": ["rating and split/join routing are not written"]},
            {"ink": "make X-999 hotter", "tag": "X-999", "confidence": 0.5,
             "change": {"path": "units.X-999.T_out_C", "value": 200}, "unreadable": []},
        ], "unreadable": ["signature"]}

    def reading(self):
        with mock.patch.object(redline, "_muse", return_value=self.raw) as muse:
            result = redline.read(self.w, png())
            cached = redline.read(self.w, png())
            muse.assert_called_once()
            self.assertEqual(result, cached)
        return result

    def test_fake_salt_read_keeps_invalid_and_incomplete_items(self):
        result = self.reading()
        self.assertEqual(len(result["items"]), 3)
        self.assertTrue(result["items"][0]["valid"])
        self.assertFalse(result["items"][1]["valid"])
        self.assertIn("needs its own limits", " ".join(result["items"][1]["errors"]))
        self.assertIn("unknown unit", " ".join(result["items"][2]["errors"]))
        self.assertEqual(result["unreadable"], ["signature"])
        self.assertTrue((redline._folder(self.w, result["id"]) / "image.png").exists())

    def test_vision_boundary_parses_fake_json_with_model_context(self):
        with mock.patch.object(redline.llm, "complete", return_value={"content": json.dumps(self.raw)}) as complete, \
                mock.patch.object(redline.llm, "set_tag"):
            result = redline.read(self.w, png())
        self.assertEqual(result["model"], "muse-wonder-1.0")
        model, messages = complete.call_args.args
        self.assertEqual(model, "muse-wonder-1.0")
        context = json.loads(messages[1]["content"][0]["text"])
        self.assertEqual(context["current_spec"], self.w.spec)
        self.assertEqual(context["equipment_and_stream_tags"], self.w.pid)
        self.assertTrue(messages[1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_confirm_validates_edits_rejections_and_hash_chain(self):
        result = self.reading()
        with self.assertRaisesRegex(ValueError, "unknown unit"):
            redline.confirm(self.w, result["id"], [{"index": 2}])
        selected = redline.confirm(self.w, result["id"], [{"index": 0, "change": {
            "path": "units.V-201.U_W_m2K", "value": 2600,
            "physical_change": "clean heater", "rating_source": "engineer corrected clean U"}}], "Alex", "reviewed red ink")
        self.assertEqual(selected["changes"][0]["value"], 2600)
        self.assertEqual(selected["rejected"], [1, 2])
        self.assertTrue(audit.verify(self.w.name)["ok"])
        entries = audit.entries(self.w.name)
        self.assertEqual(entries[-2]["details"]["ink"], "E-201 clean to U 2,500")
        self.assertEqual(entries[-1]["details"]["hash"], selected["hash"])
        self.assertEqual(self.w.spec["units"][0]["U_W_m2K"], 2000)

    def test_check_uses_real_verify_and_both_design_adapters_without_mutating_featured(self):
        result = self.reading()
        redline.confirm(self.w, result["id"], [{"index": 0}])
        original = copy.deepcopy(self.w.answers)
        solved = {"errors": [], "units": {}, "streams": {}, "checks": [
            {"id": "V-201", "check": "heater area", "utilisation": 0.8, "value": 80, "limit": 100, "unit": "m2"}]}
        def checks(workspace, index):
            value = workspace.answers[index]["proposals"][0]["changes"][0]["value"]
            return [{"check": "process", "status": "pass", "engine": "DWSIM",
                     "title": "Fake deterministic check", "numbers": {"U_W_m2K": value}}]
        with mock.patch.object(PlantWorkspace, "state", return_value=solved), \
                mock.patch.object(PlantWorkspace, "_solve", return_value=solved), \
                mock.patch.object(PlantWorkspace, "_capacity_of", return_value={"capacity_multiple": 1.3}), \
                mock.patch.object(redline.designchecks, "checks_for_design", side_effect=checks) as engine:
            compared = redline.check(self.w, result["id"])
            self.assertEqual(engine.call_count, 2)
        self.assertTrue(compared["answer"]["proposals"][0]["verified"])
        self.assertEqual(compared["engineer"][1]["numbers"]["U_W_m2K"], 2500)
        self.assertEqual(compared["muse"][0]["numbers"]["U_W_m2K"], 2400)
        self.assertEqual(self.w.answers, original)
        with mock.patch.object(redline, "check", return_value=compared), \
                mock.patch.object(redline.revb, "from_workspace", return_value={"svg": "<svg/>"}) as draw:
            self.assertEqual(redline.drawing(self.w, result["id"])["svg"], "<svg/>")
            self.assertEqual(draw.call_args.args[0].revisions, [])

    def test_unavailable_engine_is_open_and_stale_model_is_refused(self):
        result = self.reading()
        with self.assertRaisesRegex(ValueError, "confirm"):
            redline.check(self.w, result["id"])
        redline.confirm(self.w, result["id"], [{"index": 0}])
        with mock.patch.object(PlantWorkspace, "verify", side_effect=RuntimeError("DWSIM unavailable")), \
                mock.patch.object(redline.designchecks, "checks_for_design", return_value=[]):
            compared = redline.check(self.w, result["id"])
        self.assertEqual(compared["engineer"][0]["status"], "open")
        self.assertIsNone(compared["drawing_url"])
        self.w.spec["units"][0]["U_W_m2K"] = 2100
        with self.assertRaisesRegex(ValueError, "model changed"):
            redline.check(self.w, result["id"])

    def test_bad_image_ids_nonfinite_values_and_limit_edits_are_refused(self):
        with mock.patch.object(redline, "_muse") as muse:
            with self.assertRaises(ValueError):
                redline.read(self.w, b"not an image")
            muse.assert_not_called()
        with self.assertRaises(ValueError):
            redline._folder(self.w, "../../model.json")
        self.assertTrue(redline._errors(self.w.spec, [{"path": "limits.P-101.max_m3_h", "value": 200}]))
        self.assertTrue(redline._errors(self.w.spec, [{"path": "units.V-201.U_W_m2K", "value": float("nan")}]))

    def test_api_spending_gate_confirmation_and_origin(self):
        result = self.reading()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def request(path, data, origin=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            headers = {"Content-Type": "application/json"}
            if origin:
                headers["Origin"] = origin
            conn.request("POST", path, json.dumps(data), headers)
            response = conn.getresponse()
            body = response.read()
            conn.close()
            return response.status, body
        with mock.patch.object(web, "all_cases", return_value=["salt_mvr"]), \
                mock.patch.object(web, "plant", return_value=self.w), \
                mock.patch.dict(os.environ, {"WEB_ALLOW_RUNS": "0", "WEB_AUTH_TOKEN": ""}):
            self.assertEqual(request("/api/plant/salt_mvr/redline", {})[0], 403)
            path = f"/api/plant/salt_mvr/redline/{result['id']}/confirm"
            self.assertEqual(request(path, {"items": [{"index": 0}]}, "https://evil.test")[0], 403)
            self.assertEqual(request(path, {"items": [{"index": 0}]})[0], 200)
        with mock.patch.object(web, "all_cases", return_value=["salt_mvr"]), \
                mock.patch.object(web, "plant_job", return_value={"job": "fake-job"}) as job, \
                mock.patch.dict(os.environ, {"WEB_ALLOW_RUNS": "1", "WEB_AUTH_TOKEN": ""}):
            status, body = request("/api/plant/salt_mvr/redline", {"image_b64": base64.b64encode(png()).decode()})
            self.assertEqual(status, 200, body)
            self.assertEqual(json.loads(body), {"job": "fake-job"})
            job.assert_called_once()


if __name__ == "__main__":
    unittest.main()
