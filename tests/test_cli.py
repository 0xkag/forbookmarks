"""Tests for the CLI interface of forbookmarks."""

import unittest
import os
import tempfile
from click.testing import CliRunner
from forbookmarks.__main__ import main  # Assuming 'main' is the click entry point group


class TestCli(unittest.TestCase):
    """Test suite for CLI operations."""

    def setUp(self):
        """Set up test fixtures, including dummy files and a test script."""
        self.runner = CliRunner()

        # Create a dummy HTML file for testing CLI using tempfile
        self._temp_html_file_obj = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".html", encoding="utf-8"
        )
        self.test_html_file_path = self._temp_html_file_obj.name
        html_content = (
            "<!DOCTYPE NETSCAPE-Bookmark-file-1><TITLE>Bookmarks</TITLE>"
            "<H1>Bookmarks</H1><DL><p><DT>"
            '<A HREF="http://cli.example.com/test1">CLI Test 1</A></DL><p>'
        )
        self._temp_html_file_obj.write(html_content)
        self._temp_html_file_obj.flush()
        self._temp_html_file_obj.seek(
            0
        )  # Rewind for reading if necessary, though CLI runner reads by path

        # Create a dummy script for the --exec command using tempfile
        self._temp_script_file_obj = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".sh", encoding="utf-8"
        )
        self.test_script_path = self._temp_script_file_obj.name
        script_content = (
            "#!/bin/sh\necho \"URL='$BOOKMARK_URL' TITLE='$BOOKMARK_TITLE' "
            "PATH='$BOOKMARK_PATH_STR' ARGS=$*\""
        )
        self._temp_script_file_obj.write(script_content)
        self._temp_script_file_obj.flush()
        os.chmod(self.test_script_path, 0o755)
        self._temp_script_file_obj.close()  # Close the file before execution

    def tearDown(self):
        """Clean up temporary files."""
        self._temp_html_file_obj.close()
        self._temp_script_file_obj.close()
        os.remove(self.test_html_file_path)
        os.remove(self.test_script_path)

    def test_cli_html_exec_env_vars(self):
        """Test HTML processing passing data via environment variables."""
        # Testing with environment variables (default)
        result = self.runner.invoke(
            main,
            [
                "process",
                "-f",
                self.test_html_file_path,
                "-i",
                "html",
                "-x",
                self.test_script_path,
            ],
        )
        self.assertEqual(
            result.exit_code,
            0,
            msg=f"CLI Error: {result.output}, {result.exc_info}",  # noqa: E501
        )
        # Line 61: Reformatted assertIn
        expected_text_env_url = "URL='http://cli.example.com/test1'"
        self.assertIn(expected_text_env_url, result.output)  # noqa: E501
        self.assertIn("TITLE='CLI Test 1'", result.output)
        # HTML parser currently doesn't provide path, so BOOKMARK_PATH_STR would be empty
        self.assertIn("PATH=''", result.output)

    def test_cli_html_exec_args(self):
        """Test HTML processing passing data via command line arguments."""
        # Testing with command line arguments
        result = self.runner.invoke(
            main,
            [
                "process",
                "-f",
                self.test_html_file_path,
                "-i",
                "html",
                "-x",
                f"{self.test_script_path} prefix_arg",  # command with a prefix arg
                "--no-env-vars",
                "--args",
            ],
        )
        self.assertEqual(
            result.exit_code,
            0,
            msg=f"CLI Error: {result.output}, {result.exc_info}",  # noqa: E501
        )
        # Expected: prefix_arg http://cli.example.com/test1 CLI Test 1 (path elements...)
        # Path is empty for current HTML parser, path elements are not passed if path is empty
        # Line 86: Reformatted assertIn
        expected_text_args = "ARGS=prefix_arg http://cli.example.com/test1 CLI Test 1"
        self.assertIn(expected_text_args, result.output)  # noqa: E501

    def test_cli_html_exec_placeholders(self):
        """Test HTML processing using placeholders in the exec command."""
        # Testing with placeholders in the exec string
        result = self.runner.invoke(
            main,
            [
                "process",
                "-f",
                self.test_html_file_path,  # Use updated path variable
                "-i",
                "html",
                "-x",
                f'{self.test_script_path} "{{URL}}" "{{TITLE}}" "{{PATH}}"',  # Placeholders quoted
                "--no-env-vars",
                "--no-args",
            ],
        )
        self.assertEqual(
            result.exit_code,
            0,
            msg=f"CLI Error: {result.output}, {result.exc_info}",  # noqa: E501
        )
        # Expected: ARGS="http://cli.example.com/test1" "CLI Test 1" ""
        # (PATH is empty string from html parser)
        self.assertIn(
            'ARGS="http://cli.example.com/test1" "CLI Test 1" ""', result.output
        )

    def test_cli_missing_file(self):
        """Test CLI behavior when the input file is missing."""
        result = self.runner.invoke(
            main,
            ["process", "-f", "tests/nosuchfile.html", "-i", "html", "-x", "echo test"],
        )
        self.assertNotEqual(result.exit_code, 0)
        # Line 125: Reformatted assertIn & Updated error message
        # Click's error message for a non-existent file with Path(exists=True)
        expected_error_msg = "Error: Invalid value for '--input-file' / '-f': File 'tests/nosuchfile.html' does not exist."  # noqa: E501
        self.assertIn(expected_error_msg, result.output)


if __name__ == "__main__":
    unittest.main()
