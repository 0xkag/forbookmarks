# pylint: disable=broad-except, too-many-arguments, too-many-locals, too-many-branches
"""
Main CLI script for forbookmarks.
Uses click for command-line interface.
"""
import os
import subprocess
from typing import List, Dict, Iterator, Union # Removed Any

import click

# Attempt to import parsers
# Type checking for these dynamic imports can be tricky.
# We assume they are present and conform to an expected interface.
BookmarkData = Dict[str, Union[str, List[str]]]
ParserFunction = Iterator[BookmarkData]

try:
    from .parser_html import parse_html_bookmarks
    from .parser_json import parse_json_bookmarks
except ImportError:
    try:
        from parser_html import parse_html_bookmarks # type: ignore
        from parser_json import parse_json_bookmarks # type: ignore
    except ImportError:
        # This case should ideally not happen if run via poetry
        click.echo(
            "Error: Parsers not found. Ensure package is installed.",
            err=True
        )
        # To satisfy mypy about the parsers possibly not being defined:
        def parse_html_bookmarks(file_path: str) -> ParserFunction:
            """Dummy parser."""
            click.echo(f"Dummy HTML parser for {file_path}", err=True)
            return iter([])
        def parse_json_bookmarks(file_path: str) -> ParserFunction:
            """Dummy parser."""
            click.echo(f"Dummy JSON parser for {file_path}", err=True)
            return iter([])

@click.group()
def main() -> None:
    """
    A tool to process web browser bookmarks,
    similar to formail for mbox files.
    """
    # W0107: Unnecessary pass statement (unnecessary-pass) removed

@main.command()
@click.option(
    '--input-file', '-f',
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    required=True,
    help="Path to the bookmarks file."
)
@click.option(
    '--input-format', '-i',
    type=click.Choice(['html', 'json'], case_sensitive=False),
    required=True,
    help="Format of the bookmarks file."
)
@click.option(
    '--exec', '-x', 'exec_command_str',
    type=str,
    required=True,
    help="Command to execute for each bookmark. Use {URL}, {TITLE}, {PATH}."
)
@click.option(
    '--env-vars/--no-env-vars',
    default=True,
    help="Pass data as env vars (BOOKMARK_URL, etc.). Default is true."
)
@click.option(
    '--args/--no-args',
    default=False,
    help="Pass bookmark data as command line arguments."
)
@click.option(
    '--path-separator',
    default='/',
    show_default=True,
    help="Separator for folder path elements."
)
def process( # pylint: disable=too-many-arguments, too-many-locals
    input_file: str,
    input_format: str,
    exec_command_str: str,
    env_vars: bool,
    args: bool,
    path_separator: str
) -> None:
    # pylint: disable=line-too-long
    """
    Process bookmarks from the given file and execute a command for each.

    Bookmark data can be passed as:
    1. Environment variables (default): BOOKMARK_URL, BOOKMARK_TITLE,
       BOOKMARK_PATH_STR, BOOKMARK_PATH_0, ...
    2. Command line arguments (if --args is used).
    3. Placeholders in --exec: {URL}, {TITLE}, {PATH}.
    """
    # pylint: enable=line-too-long
    bookmarks: ParserFunction

    if input_format == 'html':
        bookmarks = parse_html_bookmarks(input_file)
    elif input_format == 'json':
        bookmarks = parse_json_bookmarks(input_file)
    else:
        # Should be caught by click.Choice, but as a safeguard:
        click.echo(f"Error: Unsupported input format '{input_format}'.", err=True)
        return

    bookmark_iterator: Iterator[BookmarkData] = iter(bookmarks)

    for bookmark_item in bookmark_iterator:
        url: str = str(bookmark_item.get('url', ''))
        title: str = str(bookmark_item.get('title', ''))
        path_list: List[str] = [str(p) for p in bookmark_item.get('path', []) if p]
        path_str: str = path_separator.join(path_list)

        current_env: Dict[str, str] = os.environ.copy()
        if env_vars:
            current_env['BOOKMARK_URL'] = url
            current_env['BOOKMARK_TITLE'] = title
            current_env['BOOKMARK_PATH_STR'] = path_str
            for i, part in enumerate(path_list):
                current_env[f'BOOKMARK_PATH_{i}'] = part

        # C0301: Line too long (221/100) - Reformatting
        final_command_str: str = exec_command_str.replace('{URL}', url)
        final_command_str = final_command_str.replace('{TITLE}', title)
        final_command_str = final_command_str.replace('{PATH}', path_str)

        # Using shlex.split for robust command parsing is better,
        # but for now, simple split.
        cmd_list: List[str] = final_command_str.split()

        if args:
            cmd_list.append(url)
            cmd_list.append(title)
            cmd_list.extend(path_list)

        if not cmd_list:
            click.echo("Error: Command to execute is empty.", err=True)
            continue

        click.echo(f"Executing: {' '.join(cmd_list)}")
        click.echo(f"  URL: {url}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Path: {path_str}")

        try:
            # pylint: disable=subprocess-run-check
            process_result: subprocess.CompletedProcess[str] = subprocess.run(
                cmd_list, env=current_env, capture_output=True, text=True
            )
            if process_result.stdout:
                click.echo(f"  Stdout: {process_result.stdout.strip()}")
            if process_result.stderr:
                click.echo(f"  Stderr: {process_result.stderr.strip()}", err=True)
            if process_result.returncode != 0:
                click.echo(
                    f"  Command exited with error: {process_result.returncode}",
                    err=True
                )
        except FileNotFoundError:
            click.echo(f"Error: Command not found: {cmd_list[0]}", err=True)
        except Exception as e:
            click.echo(f"Error executing '{' '.join(cmd_list)}': {e}", err=True)

if __name__ == '__main__':
    main()
