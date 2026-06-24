import unittest

from api.run import _query_params


class VercelAPITests(unittest.TestCase):
    def test_query_params_takes_last_value(self):
        params = _query_params("/api/run?topic=AI&limit=8&limit=10")
        self.assertEqual(params["topic"], "AI")
        self.assertEqual(params["limit"], "10")


if __name__ == "__main__":
    unittest.main()
