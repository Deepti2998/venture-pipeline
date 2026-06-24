import json
import unittest

from tests.test_scoring import candidate
from venture_pipeline.analysis.heuristic import HeuristicAnalyst
from venture_pipeline.analysis.llm import OpenAIAnalyst, _extract_response_text


class LLMTests(unittest.TestCase):
    def test_responses_payload_uses_structured_output(self):
        analysis = HeuristicAnalyst("AI agents for SMBs").analyze(candidate())
        payload = OpenAIAnalyst()._build_payload(analysis, "gpt-5.4-mini")
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertIn("rationale", payload["text"]["format"]["schema"]["required"])

    def test_extract_response_text_accepts_common_shapes(self):
        self.assertEqual(_extract_response_text({"output_text": "{}"}), "{}")
        body = {"output": [{"content": [{"type": "output_text", "text": json.dumps({"team": "ok"})}]}]}
        self.assertEqual(_extract_response_text(body), '{"team": "ok"}')


if __name__ == "__main__":
    unittest.main()
