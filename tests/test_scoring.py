import unittest

from venture_pipeline.analysis.scoring import recommendation_for, score_candidate
from venture_pipeline.models import Candidate, Evidence


def candidate(**overrides):
    base = Candidate(
        name="TestCo",
        website="https://testco.example",
        one_liner="AI agents for dental office billing",
        team_signal="YC Winter 2025, team size 3, Early, Healthcare",
        traction_signals=["YC batch: Winter 2025", "Status: Active", "Stage: Early", "Team size listed as 3"],
        source="yc",
        source_url="https://www.ycombinator.com/companies/testco",
        tags=["Healthcare", "Automation"],
        evidence=[
            Evidence(
                source="YC public directory",
                title="TestCo",
                url="https://www.ycombinator.com/companies/testco",
                observed_at="2026-06-24T00:00:00+00:00",
                snippet="AI agents automate revenue cycle management for small dental offices.",
                facts={
                    "batch": "Winter 2025",
                    "status": "Active",
                    "stage": "Early",
                    "team_size": 3,
                    "industry": "Healthcare",
                },
            )
        ],
        raw={},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


class ScoringTests(unittest.TestCase):
    def test_strong_vertical_ai_company_scores_above_watch_bar(self):
        item = candidate()
        score = score_candidate(item, "AI agents for SMBs")
        self.assertGreaterEqual(score.total, 55)
        self.assertIn(recommendation_for(item, score), {"Watch", "Take a meeting"})

    def test_acquired_company_is_pass_even_with_good_score(self):
        item = candidate()
        item.evidence[0].facts["status"] = "Acquired"
        score = score_candidate(item, "AI agents for SMBs")
        self.assertEqual(recommendation_for(item, score), "Pass")


if __name__ == "__main__":
    unittest.main()
