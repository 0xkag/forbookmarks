"""Tests for the JSON parser module."""

import unittest
import os
import json
from forbookmarks.parser_json import parse_json_bookmarks


class TestJsonParser(unittest.TestCase):
    """Test suite for the JSON bookmark parser."""

    def setUp(self):
        """Set up test fixtures, including sample JSON bookmark files."""
        self.chrome_test_file = "tests/sample_chrome_bookmarks.json"
        self.firefox_test_file = "tests/sample_firefox_bookmarks.json"

        # Create sample files if they don't exist
        os.makedirs("tests", exist_ok=True)  # Ensure tests directory exists
        chrome_sample_content = {
            "roots": {
                "bookmark_bar": {
                    "children": [
                        {"name": "Google", "type": "url", "url": "https://google.com"},
                        {
                            "name": "Tech Blogs",
                            "type": "folder",
                            "children": [
                                {
                                    "name": "Ars Technica",
                                    "type": "url",
                                    "url": "https://arstechnica.com",
                                }
                            ],
                        },
                    ],
                    "name": "Bookmarks bar",
                    "type": "folder",
                }
            },
            "version": 1,
        }
        # Recreate sample_chrome_bookmarks.json to ensure it's always correct for the test
        with open(self.chrome_test_file, "w", encoding="utf-8") as f:
            json.dump(chrome_sample_content, f)

        firefox_sample_content = {
            "title": "Bookmarks Menu",
            "root": "placesRoot",
            "children": [
                {
                    "title": "Mozilla Firefox",
                    "uri": "https://www.mozilla.org/firefox/",
                    "type": "text/x-moz-place",
                },
                {
                    "title": "Work Stuff",
                    "type": "text/x-moz-place-container",
                    "children": [
                        {
                            "title": "Internal Wiki",
                            "uri": "http://internal.example.com/wiki",
                            "type": "text/x-moz-place",
                        }
                    ],
                },
            ],
        }
        # Recreate sample_firefox_bookmarks.json to ensure it's always correct for the test
        with open(self.firefox_test_file, "w", encoding="utf-8") as f:
            json.dump(firefox_sample_content, f)

    def test_parse_chrome_json(self):
        """Test parsing a sample Chrome JSON bookmarks file."""
        bookmarks = list(parse_json_bookmarks(self.chrome_test_file))
        self.assertEqual(len(bookmarks), 2)
        expected_bms = [
            {"url": "https://google.com", "title": "Google", "path": ["Bookmarks bar"]},
            {
                "url": "https://arstechnica.com",
                "title": "Ars Technica",
                "path": ["Bookmarks bar", "Tech Blogs"],
            },
        ]
        for bm in expected_bms:
            self.assertIn(bm, bookmarks)

    def test_parse_firefox_json(self):
        """Test parsing a sample Firefox JSON bookmarks file."""
        bookmarks = list(parse_json_bookmarks(self.firefox_test_file))
        self.assertEqual(len(bookmarks), 2)
        expected_bms = [
            {
                "url": "https://www.mozilla.org/firefox/",
                "title": "Mozilla Firefox",
                "path": ["Bookmarks Menu"],
            },
            {
                "url": "http://internal.example.com/wiki",
                "title": "Internal Wiki",
                "path": ["Bookmarks Menu", "Work Stuff"],
            },
        ]
        for bm in expected_bms:
            self.assertIn(bm, bookmarks)

    def test_parse_non_existent_json(self):
        """Test parsing a non-existent JSON file."""
        bookmarks = list(parse_json_bookmarks("tests/non_existent.json"))
        self.assertEqual(len(bookmarks), 0)


if __name__ == "__main__":
    unittest.main()
