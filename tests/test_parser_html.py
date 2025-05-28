import unittest
import os
from forbookmarks.parser_html import parse_html_bookmarks


class TestHtmlParser(unittest.TestCase):
    def setUp(self):
        self.test_file_path = "tests/sample_bookmarks.html"
        # Create the sample file if it doesn't exist (e.g., during CI)
        # The file is already created in a previous step, but this ensures it exists if tests are run independently.
        if not os.path.exists(self.test_file_path):
            os.makedirs(os.path.dirname(self.test_file_path), exist_ok=True)
            with open(self.test_file_path, "w", encoding="utf-8") as f:
                f.write(
                    """
                <!DOCTYPE NETSCAPE-Bookmark-file-1>
                <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
                <TITLE>Bookmarks</TITLE>
                <H1>Bookmarks</H1>
                <DL><p>
                    <DT><H3 ADD_DATE="1600000000" LAST_MODIFIED="1600000000">Folder1</H3>
                    <DL><p>
                        <DT><A HREF="http://example.com/page1" ADD_DATE="1600000001">Example Page 1</A>
                        <DT><A HREF="https://example.org/page2" ADD_DATE="1600000002">Example Page 2</A>
                    </DL><p>
                    <DT><A HREF="http://no-folder-example.com" ADD_DATE="1600000003">No Folder Example</A>
                </DL><p>
                """
                )

    def test_parse_sample_html(self):
        bookmarks = list(parse_html_bookmarks(self.test_file_path))
        self.assertEqual(len(bookmarks), 3)

        self.assertIn(
            {
                "url": "http://example.com/page1",
                "title": "Example Page 1",
                "path": [],  # Path extraction not yet in simple HTML parser
            },
            bookmarks,
        )
        self.assertIn(
            {
                "url": "https://example.org/page2",
                "title": "Example Page 2",
                "path": [],  # Path extraction not yet in simple HTML parser
            },
            bookmarks,
        )
        self.assertIn(
            {
                "url": "http://no-folder-example.com",
                "title": "No Folder Example",
                "path": [],  # Path extraction not yet in simple HTML parser
            },
            bookmarks,
        )

    def test_parse_non_existent_html(self):
        bookmarks = list(parse_html_bookmarks("tests/non_existent.html"))
        self.assertEqual(len(bookmarks), 0)


if __name__ == "__main__":
    unittest.main()
