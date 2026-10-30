"""Regression tests for the local web server's untrusted inputs."""
import base64
import http.client
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import pymupdf

from plantagent import audit, web


class WebSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "runs" / "sample" / "run1").mkdir(parents=True)
        (self.root / "runs" / "sample" / "run1" / "log.jsonl").write_text("{}\n")
        (self.root / "web").mkdir()
        for attr, value in (("ROOT", self.root), ("RUNS", self.root / "runs"), ("STATIC", self.root / "web"),
                            ("DATA_ROOT", self.root / "data")):
            patch = mock.patch.object(web, attr, value)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(web, "all_cases", side_effect=lambda kind="study": ["sample"])
        patch.start()
        self.addCleanup(patch.stop)
        env = mock.patch.dict(os.environ, {"WEB_AUTH_TOKEN": "", "WEB_ALLOW_WRITES": "0"})
        env.start()
        self.addCleanup(env.stop)
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
        status = response.status
        conn.close()
        return status, data

    def test_run_and_workspace_files_cannot_escape_or_expose_internal_logs(self):
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        outside = Path(other.name) / "secret.txt"
        outside.write_text("secret")
        run = self.root / "runs" / "sample" / "run1"
        (run / "report.md").symlink_to(outside)
        (run / "study.json").symlink_to(outside)
        self.assertEqual(self.request("GET", "/files/sample/run1/report.md")[0], 404)
        self.assertEqual(self.request("GET", "/api/run/sample/run1/detail")[0], 400)
        self.assertEqual(self.request("GET", "/api/run/sample/../detail")[0], 404)
        ws = self.root / "runs" / "ws" / "sample" / "session"
        ws.mkdir(parents=True)
        (ws / "log.jsonl").write_text("private")
        (ws / "memo.md").symlink_to(outside)
        self.assertEqual(self.request("GET", "/wsfiles/sample/session/log.jsonl")[0], 404)
        self.assertEqual(self.request("GET", "/wsfiles/sample/session/memo.md")[0], 404)
        (run / "report.md").unlink()
        (run / "report.md").write_text("public")
        self.assertEqual(self.request("GET", "/files/sample/run1/report.md"), (200, b"public"))

    def test_rejects_malformed_and_oversized_posts_before_parsing(self):
        self.assertEqual(self.request("POST", "/api/newproject", b"[1]", {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("POST", "/api/newproject", b"{", {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("POST", "/api/newproject", b"x", {"Content-Length": str(web.MAX_POST + 1)})[0], 413)
        self.assertEqual(self.request("POST", "/api/ws/sample/model", b"{}")[0], 400)
        self.assertEqual(self.request("GET", "/api/ws/sample/page?doc=x&n=1&dpi=100000")[0], 400)
        with mock.patch.dict("os.environ", {"WEB_ALLOW_RUNS": "1"}):
            self.assertEqual(self.request("POST", "/api/ws/sample/readsheet", b"not pdf")[0], 400)
            self.assertEqual(self.request("POST", "/api/ws/sample/voice", b"not wav")[0], 400)

    def test_muse_routes_are_disabled_without_opt_in(self):
        with mock.patch.dict("os.environ", {"WEB_ALLOW_RUNS": "0"}):
            for path in ("/api/start/sample", "/api/plant/sample/build", "/api/plant/sample/ask",
                         "/api/ws/sample/ask", "/api/ws/sample/task", "/api/ws/sample/fixall",
                         "/api/ws/sample/photo", "/api/ws/sample/voice", "/api/ws/sample/readsheet"):
                with self.subTest(path=path):
                    self.assertEqual(self.request("POST", path, b"{}")[0], 403)
            self.assertEqual(self.request("POST", "/api/ws/sample/export", b'{"kind":"memo"}',
                                          {"Content-Type": "application/json"})[0], 403)

    def test_configured_server_requires_bearer_and_remote_writes_are_opt_in(self):
        with mock.patch.dict(os.environ, {"WEB_AUTH_TOKEN": "secret", "WEB_ALLOW_WRITES": "0"}):
            self.assertEqual(self.request("GET", "/api/job/nope")[0], 403)
            auth = {"Authorization": "Bearer secret"}
            self.assertEqual(self.request("GET", "/api/job/nope", headers=auth)[0], 404)
            self.assertEqual(self.request("POST", "/api/newproject", b"{}", {**auth, "Content-Type": "application/json"})[0], 403)

    def test_forwarded_local_request_is_treated_as_remote(self):
        self.assertEqual(self.request("GET", "/api/job/nope", headers={"X-Forwarded-For": "203.0.113.4"})[0], 403)

    def test_one_mutating_job_per_case(self):
        job = web._new_job("sample")
        self.addCleanup(lambda: web._finish_job("sample", job) if not web.JOBS[job]["done"] else None)
        with self.assertRaises(web.BusyError):
            web._new_job("sample")
        with self.assertRaises(web.BusyError):
            web._case_call("sample", lambda: None)
        web._finish_job("sample", job)
        self.assertEqual(web._case_call("sample", lambda: "ok"), "ok")
        second = web._new_job("sample")
        web._finish_job("sample", second)


class ProjectAndAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "cases").mkdir()
        (self.root / "data").mkdir()
        for module, attr, value in ((web, "ROOT", self.root), (web, "DATA_ROOT", self.root / "data"),
                                    (audit, "ROOT", self.root)):
            patch = mock.patch.object(module, attr, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.project = {"title": "Unit Test", "question": "How much capacity is available?",
                        "data_sheet": "flow and pressure: " * 15, "drawing_name": "drawing.xml",
                        "drawing_b64": base64.b64encode(b'<PlantModel><Equipment ID="E1" ComponentClass="Pump"/></PlantModel>').decode()}

    def test_upload_validation_and_bounded_slug_collision(self):
        for change in ({"drawing_b64": "!!!!"}, {"drawing_b64": "a" * (4 * ((web.MAX_UPLOAD + 2) // 3) + 1)},
                       {"drawing_b64": base64.b64encode(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><PlantModel/>').decode()},
                       {"drawing_b64": base64.b64encode('<!DOCTYPE x [<!ENTITY e "boom">]><PlantModel/>'.encode("utf-16")).decode()},
                       {"drawing_name": "drawing.pdf", "drawing_b64": base64.b64encode(b"not a PDF").decode()},
                       {"target_scale": "NaN"}):
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError):
                    web.new_project({**self.project, **change})
        first = web.new_project(self.project)
        second = web.new_project(self.project)
        self.assertEqual((first["case"], second["case"]), ("unit_test", "unit_test_2"))
        self.assertTrue(audit.verify("unit_test")["ok"])

    def test_valid_pdf_is_opened_and_closed(self):
        pdf = pymupdf.open()
        pdf.new_page()
        data = pdf.tobytes()
        pdf.close()
        result = web.new_project({**self.project, "drawing_name": "plan.pdf", "drawing_b64": base64.b64encode(data).decode()})
        self.assertEqual(result["case"], "unit_test")

    def test_uploaded_project_defaults_to_non_contributor_model(self):
        result = web.new_project(self.project)
        web.PLANTS.pop(result["case"], None)
        self.addCleanup(lambda: web.PLANTS.pop(result["case"], None))
        with mock.patch("plantagent.plant.PlantWorkspace") as workspace:
            web.plant(result["case"])
        workspace.assert_called_once_with(result["case"], "muse-spark-1.3")

    def test_audit_append_is_serial_and_claimed_identity_is_not_authenticated(self):
        with ThreadPoolExecutor(8) as pool:
            list(pool.map(lambda _: audit.append("unit_test", "edit", "alice"), range(40)))
        self.assertEqual(audit.verify("unit_test"), {"ok": True, "entries": 40})
        self.assertEqual(audit.entries("unit_test")[0]["user"], "claimed: alice")
        with self.assertRaises(ValueError):
            audit.entries("../secret")
        f = audit._file("unit_test")
        lines = f.read_text().splitlines()
        tampered = json.loads(lines[0])
        tampered["reason"] = "changed"
        f.write_text(json.dumps(tampered) + "\n" + "\n".join(lines[1:]) + "\n")
        self.assertEqual(audit.verify("unit_test")["broken_at"], 1)

    def test_audit_checkpoint_detects_tail_deletion(self):
        audit.append("unit_test", "one")
        audit.append("unit_test", "two")
        path = audit._file("unit_test")
        path.write_text(path.read_text().splitlines()[0] + "\n")
        self.assertEqual(audit.verify("unit_test"), {"ok": False, "broken_at": 2, "entries": 1})


if __name__ == "__main__":
    unittest.main()
