import unittest

from venture_pipeline.analysis.heuristic import HeuristicAnalyst
from venture_pipeline.render.memo import memo_filename, render_memo
from tests.test_scoring import candidate


class MemoTests(unittest.TestCase):
    def test_memo_contains_call_score_and_evidence(self):
        analysis = HeuristicAnalyst("AI agents for SMBs").analyze(candidate())
        memo = render_memo(analysis)
        self.assertIn("**Call:**", memo)
        self.assertIn("**Score:**", memo)
        self.assertIn("## Evidence", memo)
        self.assertIn("YC public directory", memo)

    def test_memo_filename_is_markdown(self):
        analysis = HeuristicAnalyst("AI agents for SMBs").analyze(candidate())
        self.assertTrue(memo_filename(analysis).endswith("-testco.md"))


if __name__ == "__main__":
    unittest.main()
