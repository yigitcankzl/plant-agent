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


class TextCalls(unittest.TestCase):
    def test_function_tag_form_is_recovered(self):
        text = '<function name="answer">\n<parameter name="headline">12% with valves</parameter>\n<parameter name="proposals">[{"title": "x"}]</parameter>\n</function>'
        self.assertTrue(study.TEXT_CALL.search(text))
        calls = study.text_tool_calls(text)
        self.assertEqual(calls[0]["name"], "answer")
        self.assertEqual(__import__("json").loads(calls[0]["arguments"])["proposals"], [{"title": "x"}])

    def test_bare_tool_tag_form_is_recovered(self):
        text = '<answer>\n<parameter name="headline">47% more flow</parameter>\n<parameter name="cards">[{"title": "a"}]</parameter>'
        self.assertTrue(study.TEXT_CALL.search(text))
        calls = study.text_tool_calls(text)
        self.assertEqual(calls[0]["name"], "answer")
        self.assertEqual(__import__("json").loads(calls[0]["arguments"])["cards"], [{"title": "a"}])
        self.assertFalse(study.TEXT_CALL.search("<b>bold</b> prose"))

    def test_invoke_form_still_works(self):
        self.assertEqual(study.text_tool_calls('<x:invoke name="run"><x:parameter name="a">1</x:parameter></x:invoke>')[0]["name"], "run")
