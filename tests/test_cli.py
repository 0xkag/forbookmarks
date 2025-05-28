import unittest
import os
from click.testing import CliRunner
from forbookmarks.__main__ import main # Assuming 'main' is the click entry point group

class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        # Create a dummy HTML file for testing CLI
        self.test_html_file = "tests/cli_test_bookmarks.html"
        os.makedirs(os.path.dirname(self.test_html_file), exist_ok=True) # Ensure dir exists
        with open(self.test_html_file, "w", encoding="utf-8") as f:
            f.write("""
            <!DOCTYPE NETSCAPE-Bookmark-file-1><TITLE>Bookmarks</TITLE><H1>Bookmarks</H1><DL><p>
            <DT><A HREF="http://cli.example.com/test1">CLI Test 1</A></DL><p>
            """)
        
        # Create a dummy script for the --exec command
        self.test_script_path = "tests/test_exec_script.sh"
        with open(self.test_script_path, "w", encoding="utf-8") as f:
            # Added quotes around variables for robustness with spaces in titles/paths
            f.write("#!/bin/sh\necho \"URL='$BOOKMARK_URL' TITLE='$BOOKMARK_TITLE' PATH='$BOOKMARK_PATH_STR' ARGS=$*\"")
        os.chmod(self.test_script_path, 0o755)


    def tearDown(self):
        if os.path.exists(self.test_html_file):
            os.remove(self.test_html_file)
        if os.path.exists(self.test_script_path):
            os.remove(self.test_script_path)
        # if os.path.exists("tests/output_env.txt"): # Cleanup for placeholder test from original instructions, not used here
        #     os.remove("tests/output_env.txt")


    def test_cli_html_exec_env_vars(self):
        # Testing with environment variables (default)
        result = self.runner.invoke(
            main,
            [
                'process',
                '-f', self.test_html_file,
                '-i', 'html',
                '-x', f'{self.test_script_path}' 
            ]
        )
        self.assertEqual(result.exit_code, 0, msg=f"CLI Error: {result.output} {result.exception} {result.exc_info}")
        self.assertIn("URL='http://cli.example.com/test1'", result.output)
        self.assertIn("TITLE='CLI Test 1'", result.output)
        # HTML parser currently doesn't provide path, so BOOKMARK_PATH_STR would be empty
        self.assertIn("PATH=''", result.output) 

    def test_cli_html_exec_args(self):
        # Testing with command line arguments
        result = self.runner.invoke(
            main,
            [
                'process',
                '-f', self.test_html_file,
                '-i', 'html',
                '-x', f'{self.test_script_path} prefix_arg', # command with a prefix arg
                '--no-env-vars', 
                '--args'
            ]
        )
        self.assertEqual(result.exit_code, 0, msg=f"CLI Error: {result.output} {result.exception} {result.exc_info}")
        # Expected: prefix_arg http://cli.example.com/test1 CLI Test 1 (path elements...)
        # Path is empty for current HTML parser, path elements are not passed if path is empty
        self.assertIn("ARGS=prefix_arg http://cli.example.com/test1 CLI Test 1", result.output)

    def test_cli_html_exec_placeholders(self):
        # Testing with placeholders in the exec string
        result = self.runner.invoke(
            main,
            [
                'process',
                '-f', self.test_html_file,
                '-i', 'html',
                '-x', f'{self.test_script_path} "{{URL}}" "{{TITLE}}" "{{PATH}}"', # Placeholders quoted
                '--no-env-vars',
                '--no-args'
            ]
        )
        self.assertEqual(result.exit_code, 0, msg=f"CLI Error: {result.output} {result.exception} {result.exc_info}")
        # Expected: ARGS="http://cli.example.com/test1" "CLI Test 1" ""
        # (PATH is empty string from html parser)
        self.assertIn("ARGS=\"http://cli.example.com/test1\" \"CLI Test 1\" \"\"", result.output)


    def test_cli_missing_file(self):
        result = self.runner.invoke(
            main,
            ['process', '-f', 'tests/nosuchfile.html', '-i', 'html', '-x', 'echo test']
        )
        self.assertNotEqual(result.exit_code, 0) 
        self.assertIn("Error: Invalid value for '--input-file' / '-f': Path 'tests/nosuchfile.html' does not exist.", result.output)

if __name__ == '__main__':
    unittest.main()
