import unittest
from unittest import mock
from plantagent import study


class StepLimit(unittest.TestCase):
    def test_last_steps_offer_only_the_submit_tool(self):
        tools = [{"type": "function", "function": {"name": n, "parameters": {}}} for n in ("run", "answer")]
        seen = []

        def complete(model, messages, tools=None):
            seen.append([t["function"]["name"] for t in tools])
            name = "answer" if len(tools) == 1 else "run"
            return {"content": "", "tool_calls": [{"id": str(len(seen)), "name": name, "arguments": "{}"}]}

        s = study.Study.__new__(study.Study)
        s.model, s.steps, s._artifacts = "m", 0, []
        s.log = mock.MagicMock(); s.emit = lambda e: None; s.call = lambda n, a: {"ok": True}
        with mock.patch.object(study.llm, "complete", complete):
            self.assertEqual(s.loop("ask", "sys", "user", tools, "answer", 6), {})
        self.assertEqual(seen[:3], [["run", "answer"]] * 3)
        self.assertEqual(seen[3], ["answer"])


if __name__ == "__main__":
    unittest.main()
