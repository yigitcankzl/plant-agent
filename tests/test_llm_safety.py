import json
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from plantagent import llm


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls += 1
        time.sleep(0.02)
        message = SimpleNamespace(content="ok", tool_calls=[])
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


class LlmSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.patches = [mock.patch.object(llm, "ROOT", root), mock.patch.object(llm, "CACHE", root / "cache"),
                        mock.patch.object(llm, "LEDGER", root / "usage.jsonl")]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_concurrent_identical_call_is_billed_once_and_keeps_thread_tag(self):
        client = FakeClient()

        def call():
            llm.set_tag("case-a")
            return llm.complete("muse-spark-1.3", [{"role": "user", "content": "hello"}], max_tokens=10)

        with mock.patch.object(llm, "_client_for", return_value=(client, "muse-spark-1.3")):
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(lambda _: call(), range(2)))
        self.assertEqual(results, [{"content": "ok", "tool_calls": []}] * 2)
        self.assertEqual(client.calls, 1)
        rows = [json.loads(line) for line in llm.LEDGER.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tag"], "case-a")

    def test_budget_reservation_blocks_before_the_api_call(self):
        client = FakeClient()
        with mock.patch.object(llm, "BUDGET_USD", 0.000001), \
             mock.patch.object(llm, "_client_for", return_value=(client, "muse-spark-1.3")):
            with self.assertRaisesRegex(RuntimeError, "would be exceeded"):
                llm.complete("muse-spark-1.3", [{"role": "user", "content": "hello"}], max_tokens=100)
        self.assertEqual(client.calls, 0)

    def test_per_run_cap_blocks_before_the_api_call(self):
        client = FakeClient()
        with mock.patch.object(llm, "_client_for", return_value=(client, "muse-spark-1.3")), \
             llm.spend_cap(0.000001):
            with self.assertRaisesRegex(llm.BudgetExceeded, "run budget"):
                llm.complete("muse-spark-1.3", [{"role": "user", "content": "hello"}], max_tokens=100)
        self.assertEqual(client.calls, 0)

    def test_open_model_usage_keeps_provider_and_case_tag(self):
        client = FakeClient()
        llm.set_tag("plant:salt_mvr")
        model = "baseten:meta-models/muse-spark-open-1026"
        with mock.patch.object(llm, "_client_for", return_value=(client, model.split(":", 1)[1])):
            llm.complete(model, [{"role": "user", "content": "hello"}], max_tokens=10)
        row = json.loads(llm.LEDGER.read_text())
        self.assertEqual((row["provider"], row["tag"]), ("baseten", "plant:salt_mvr"))
        self.assertGreater(llm.spent("baseten"), 0)

    def test_spend_tag_can_be_inherited_by_worker_threads(self):
        llm.set_tag("sheet:one")
        with ThreadPoolExecutor(1) as pool:
            self.assertEqual(pool.submit(llm.inherit_tag(llm.current_tag)).result(), "sheet:one")


if __name__ == "__main__":
    unittest.main()
