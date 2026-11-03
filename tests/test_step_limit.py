import json
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


class BareJsonTest(unittest.TestCase):
    def test_bare_json_answer(self):
        from plantagent.study import bare_json
        self.assertEqual(bare_json('```json\n{"headline": "x", "summary": "y"}\n```')["headline"], "x")
        self.assertIsNone(bare_json('{"label": "run"}'))
        self.assertIsNone(bare_json("I will now check the flood."))


class AnswerFormsTest(unittest.TestCase):
    def test_argument_tags(self):
        from plantagent.study import text_tool_calls, TEXT_CALL
        c = '<answer>\n<argument name="headline">H</argument>\n<argument name="cards">[{"a": 1}]</argument>\n</answer>'
        self.assertTrue(TEXT_CALL.search(c))
        args = json.loads(text_tool_calls(c)[0]["arguments"])
        self.assertEqual(args, {"headline": "H", "cards": [{"a": 1}]})

    def test_attributes(self):
        from plantagent.study import text_tool_calls, TEXT_CALL
        c = '<answer headline="Rerate" summary="x" cost_class="<$100k" proposals=\'[{"title": "t"}]\'></answer>'
        self.assertTrue(TEXT_CALL.search(c))
        call = text_tool_calls(c)[0]
        self.assertEqual(call["name"], "answer")
        self.assertEqual(json.loads(call["arguments"])["proposals"], [{"title": "t"}])
        self.assertIsNone(TEXT_CALL.search('see <a href="x">the run</a>'))


class VendorTagTest(unittest.TestCase):
    def test_uppercase_vendor_tags(self):
        from plantagent.study import text_tool_calls, TEXT_CALL
        c = '<ATEM:FUNCALL name="answer">\n<ATEM:PARAM name="headline">H</ATEM:PARAM>\n<ATEM:PARAM name="status">ok</ATEM:PARAM>\n</ATEM:FUNCALL>'
        self.assertTrue(TEXT_CALL.search(c))
        call = text_tool_calls(c)[0]
        self.assertEqual((call["name"], json.loads(call["arguments"])), ("answer", {"headline": "H", "status": "ok"}))


class OfferedToolsTest(unittest.TestCase):
    def test_text_call_to_a_tool_not_offered_is_not_run(self):
        tools = [{"type": "function", "function": {"name": n, "parameters": {}}} for n in ("run", "answer")]
        ran, n = [], [0]

        def complete(model, messages, tools=None):
            n[0] += 1
            if len(tools) == 1 and n[0] == 4:  # first forced step: the model still writes a 'run' call as text
                return {"content": '<invoke name="run"><parameter name="x">1</parameter></invoke>', "tool_calls": []}
            return {"content": "", "tool_calls": [{"id": str(n[0]), "name": "answer" if len(tools) == 1 else "noop", "arguments": "{}"}]}

        s = study.Study.__new__(study.Study)
        s.model, s.steps, s._artifacts = "m", 0, []
        s.log = mock.MagicMock(); s.emit = lambda e: None
        s.call = lambda name, a: ran.append(name) or {"ok": True}
        with mock.patch.object(study.llm, "complete", complete):
            s.loop("ask", "sys", "user", tools, "answer", 6)
        self.assertNotIn("run", ran)
