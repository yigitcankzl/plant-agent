import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

from PIL import Image

from plantagent import llm, sam, pidvision
from tools.pid_read_eval import score


class SamTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for field, value in {"ROOT": root, "CACHE": root / "cache", "LEDGER": root / "usage.jsonl", "BUDGET_USD": 10}.items():
            patch = mock.patch.object(llm, field, value)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.dict(os.environ, {"META_API_KEY": "test-only", "META_BASE_URL": "https://example.invalid/v1"})
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.object(llm, "_load_env")
        patch.start()
        self.addCleanup(patch.stop)
        image = io.BytesIO()
        Image.new("RGB", (12, 10), "white").save(image, "PNG")
        self.png = image.getvalue()

    def test_response_request_cache_and_usage(self):
        response = {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": ""}]}]}
        with mock.patch.object(sam.urllib.request, "urlopen") as send:
            send.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
            result = sam.segment(self.png, ["pump"])
            self.assertEqual(sam.segment(self.png, ["pump"]), result)
            send.assert_called_once()
            request = send.call_args.args[0]
            self.assertEqual(request.full_url, "https://example.invalid/v1/responses")
            body = json.loads(request.data)
            self.assertEqual(body["model"], "sam-3.1")
            self.assertEqual(body["input"][0]["content"][0], {"type": "input_text", "text": "pump"})
            self.assertTrue(body["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,"))
            self.assertEqual(body["metadata"]["mask_encoding"], "one_bit")
        self.assertAlmostEqual(llm.spent(), .0025)

    def test_task_cap_blocks_before_network(self):
        with mock.patch.object(sam.urllib.request, "urlopen") as send, llm.spend_cap(.001):
            with self.assertRaises(llm.BudgetExceeded):
                sam.segment(self.png, ["pump"])
            send.assert_not_called()

    def test_fake_wire_masks_build_overlay_crops_and_coordinate_prompt(self):
        # Meta's documented 27x60 lossless example, translated onto a synthetic sheet.
        payload = "~!!!!M!0c[0o91w?q1!pIH4pPRVp2B3'7`e.ioeAf6-k/#Xd8%dX9x("
        wire = "<0f>7<|box;x1=5;y1=10;x2=64;y2=36;w=120;h=80|><|mask;x=0;y=0;data=27,60," + payload + "|>"
        response = {"outputs": [{"prompt": "vessel", "response": {"status": "completed", "output": [
            {"content": [{"type": "output_text", "text": wire}]}]}}]}
        png = io.BytesIO()
        Image.new("RGB", (120, 80), "white").save(png, "PNG")
        folder = llm.ROOT / "regions"
        manifest = sam.assistance(png.getvalue(), response, folder)
        self.assertEqual(manifest["regions"][0]["box_px"], [5, 10, 65, 37])
        self.assertEqual(manifest["regions"][0]["object_id"], "7")
        for file in ("R001-mask.png", "R001-crop.png", "overlay.png", "overlay.jpg", "crops.jpg", "regions.json"):
            self.assertTrue((folder / file).is_file(), file)
        parts = pidvision.sam_content(manifest, folder)
        self.assertIn('"box_px": [5, 10, 65, 37]', parts[0]["text"])
        self.assertIn("unverified guesses", parts[0]["text"])
        self.assertEqual(len(parts), 3)

    def test_assisted_empty_model_response_is_saved_without_retry(self):
        import pymupdf
        pdf = llm.ROOT / "drawing.pdf"
        with pymupdf.open() as doc:
            doc.new_page()
            doc.save(pdf)
        folder = llm.ROOT / "read"
        with mock.patch.object(sam, "segment", return_value={"outputs": []}), \
                mock.patch.object(sam, "assistance", return_value={"regions": []}), \
                mock.patch.object(llm, "complete", return_value={"content": None}) as complete:
            with self.assertRaisesRegex(ValueError, "no JSON content"):
                pidvision.read(pdf, sam_assisted=True, sam_dir=folder)
            complete.assert_called_once()
        self.assertIsNone(json.loads((folder / "read_failure.json").read_text())["message"]["content"])

    def test_disabled_flag_keeps_original_messages_and_parameters(self):
        import pymupdf
        import base64
        pdf = llm.ROOT / "drawing.pdf"
        with pymupdf.open() as doc:
            page = doc.new_page(width=120, height=80)
            page.insert_text((10, 30), "PUMP")
            doc.save(pdf)
        with pymupdf.open(pdf) as doc:
            page = doc[0]
            png = page.get_pixmap(dpi=170).tobytes("png")
            labels = [{"text": x["text"], "x": round(x["bbox"][0] / 120, 3), "y": round(x["bbox"][1] / 80, 3)}
                      for x in pidvision._labels(page)]
        expected = [{"role": "system", "content": pidvision.PROMPT}, {"role": "user", "content": [
            {"type": "text", "text": "Printed labels (x, y as fractions of the sheet): " + json.dumps(labels)},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}]}]
        raw = {"title": "Test drawing", "loops": [], "equipment": [], "connections": [], "notes": []}
        with mock.patch.object(sam, "segment", side_effect=AssertionError("SAM disabled")), \
                mock.patch.object(llm, "complete", return_value={"content": json.dumps(raw)}) as complete, \
                mock.patch.dict(os.environ, {"PID_SAM": "0"}):
            result = pidvision.read(pdf)
            self.assertNotIn("sam", result)
            self.assertEqual(complete.call_args.args, ("muse-spark-1.3-contributor", expected))
            self.assertEqual(complete.call_args.kwargs, {"response_format": {"type": "json_schema", "json_schema": {
                "name": "schematic", "schema": pidvision.SCHEMA, "strict": True}}})
            with mock.patch.dict(os.environ, {"PID_SAM": "1"}):
                pidvision.read(pdf, sam_assisted=False)
                self.assertEqual(complete.call_args.args[1], expected)

    def test_zero_regions_do_not_send_decorative_images(self):
        parts = pidvision.sam_content({"regions": []}, llm.ROOT / "not-created")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["type"], "text")
        self.assertIn("zero regions", parts[0]["text"])

    def test_http_failure_is_not_retried_or_replaced(self):
        error = urllib.error.HTTPError("https://example.invalid/v1/responses", 403, "Forbidden", {}, io.BytesIO(b'{"error":"no access"}'))
        with mock.patch.object(sam.urllib.request, "urlopen", side_effect=error) as send:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                sam.segment(self.png, ["pump", "vessel"])
            self.assertEqual(caught.exception.code, 403)
            self.assertEqual(caught.exception.read(), b'{"error":"no access"}')
            send.assert_called_once()
        self.assertEqual(llm.spent(), 0)

    def test_eval_matches_printed_labels_and_counts_direction_and_duplicates(self):
        truth = {"equipment": [{"tag": "P1", "label_text": "Pump", "class": "pump"},
                               {"tag": "V1", "label_text": "Vessel", "class": "vessel"}],
                 "connections": [{"from": "P1", "to": "V1", "loop": "10"}]}
        read = {"equipment": [{"tag": "RENAMED", "label_text": "Pump", "class": "Pump"},
                              {"tag": "TANK", "label_text": "Vessel", "class": "pump"}],
                "connections": [{"from": "RENAMED", "to": "TANK", "loop": "10"},
                                {"from": "RENAMED", "to": "TANK", "loop": "10"},
                                {"from": "TANK", "to": "RENAMED", "loop": "10"}]}
        result = score(read, truth)
        self.assertEqual(result["equipment"]["found"], 2)
        self.assertEqual(result["equipment"]["type_correct"], 1)
        self.assertEqual({k: result["connections"][k] for k in ("correct", "missing", "extra")},
                         {"correct": 1, "missing": 0, "extra": 2})
        read["connections"] = [{"from": "TANK", "to": "RENAMED", "loop": "10"}]
        self.assertEqual(score(read, truth)["connections"]["missing"], 1)


if __name__ == "__main__":
    unittest.main()
