import unittest

from venture_pipeline.sources.url_list import _MetadataParser, _normalize_url


class URLSourceTests(unittest.TestCase):
    def test_metadata_parser_extracts_title_and_description(self):
        parser = _MetadataParser()
        parser.feed(
            """
            <html>
              <head>
                <title>ExampleCo | AI billing</title>
                <meta name="description" content="AI agents for clinic billing teams">
                <meta property="og:site_name" content="ExampleCo">
              </head>
            </html>
            """
        )
        self.assertEqual(parser.title, "ExampleCo | AI billing")
        self.assertEqual(parser.meta["description"], "AI agents for clinic billing teams")
        self.assertEqual(parser.meta["og:site_name"], "ExampleCo")

    def test_normalize_url_adds_https(self):
        self.assertEqual(_normalize_url("example.com"), "https://example.com")


if __name__ == "__main__":
    unittest.main()
