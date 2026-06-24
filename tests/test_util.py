import unittest

from venture_pipeline.util import batch_to_slug, expanded_topic_terms, slugify


class UtilTests(unittest.TestCase):
    def test_batch_to_slug_accepts_short_and_long_forms(self):
        self.assertEqual(batch_to_slug("W25"), "winter-2025")
        self.assertEqual(batch_to_slug("Winter 2025"), "winter-2025")
        self.assertEqual(batch_to_slug("SP26"), "spring-2026")
        self.assertEqual(batch_to_slug("F24"), "fall-2024")

    def test_expanded_topic_terms_adds_smb_synonyms(self):
        terms = expanded_topic_terms("AI agents for SMBs")
        self.assertIn("automation", terms)
        self.assertIn("small", terms)
        self.assertIn("businesses", terms)

    def test_slugify(self):
        self.assertEqual(slugify("AI Agents for SMBs!"), "ai-agents-for-smbs")

    def test_compact_whitespace_normalizes_unicode_punctuation(self):
        from venture_pipeline.util import compact_whitespace

        self.assertEqual(compact_whitespace("We\u2019re fast\u2014really fast"), "We're fast - really fast")


if __name__ == "__main__":
    unittest.main()
