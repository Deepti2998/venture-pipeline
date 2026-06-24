import os
import tempfile
import unittest
from pathlib import Path

from venture_pipeline.env import load_env_file


class EnvTests(unittest.TestCase):
    def test_load_env_file_does_not_override_existing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("OPENAI_MODEL=gpt-5.4-mini\nCUSTOM_FLAG=yes\n", encoding="utf-8")
            os.environ["OPENAI_MODEL"] = "already-set"
            try:
                loaded = load_env_file(path)
                self.assertEqual(os.environ["OPENAI_MODEL"], "already-set")
                self.assertIn("CUSTOM_FLAG", loaded)
                self.assertEqual(os.environ["CUSTOM_FLAG"], "yes")
            finally:
                os.environ.pop("OPENAI_MODEL", None)
                os.environ.pop("CUSTOM_FLAG", None)


if __name__ == "__main__":
    unittest.main()
