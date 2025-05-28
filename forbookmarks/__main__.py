import click
import subprocess
import os # For environment variables

# Attempt to import parsers
try:
    from .parser_html import parse_html_bookmarks
    from .parser_json import parse_json_bookmarks
except ImportError:
    # This allows the script to be run directly for development/testing if parsers are in the same dir,
    # but for package structure, the relative import is preferred.
    # If Poetry/pip installs it, `from .parser_...` is correct.
    # If running `python forbookmarks/__main__.py` directly from project root, this might fail.
    # Proper execution via `poetry run forbookmarks ...` should work.
    try:
        from parser_html import parse_html_bookmarks
        from parser_json import parse_json_bookmarks
    except ImportError:
        # Fallback for when __main__ is executed as a script and parsers are not found.
        # This indicates an issue with how the script is run or PYTHONPATH.
        # For now, we'll let it raise an error if they are truly missing.
        click.echo("Error: Parsers not found. Ensure the package is installed correctly or running from the correct directory.", err=True)
        # A more robust solution might involve adjusting sys.path or having a different entry point for direct script execution.
        # However, for a poetry project, `poetry run` is the standard.
        # We will assume for now that if this fails, the user needs to run with poetry.
        pass


@click.group()
def main():
    """
    A tool to process web browser bookmarks, similar to formail for mbox files.
    """
    pass

@main.command()
@click.option(
    '--input-file', '-f',
    type=click.Path(exists=True, dir_okay=False, readable=True),
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
    '--exec', '-x', 'exec_command_str', # Renamed to avoid conflict with exec keyword
    type=str,
    required=True,
    help="Command to execute for each bookmark. Use {URL}, {TITLE}, {PATH} placeholders."
)
@click.option(
    '--env-vars / --no-env-vars',
    default=True, # Provide data as environment variables by default
    help="Pass bookmark data as environment variables (BOOKMARK_URL, BOOKMARK_TITLE, BOOKMARK_PATH_STR, BOOKMARK_PATH_0, ...). Default is true."
)
@click.option(
    '--args / --no-args',
    default=False, # Do not pass as command line arguments by default
    help="Pass bookmark data as command line arguments to the executed command. Note: this appends to the command string. Ensure your command handles extra arguments."
)
@click.option(
    '--path-separator',
    default='/',
    show_default=True,
    help="Separator for joining folder path elements in BOOKMARK_PATH_STR or for command line arguments."
)
def process(input_file, input_format, exec_command_str, env_vars, args, path_separator):
    """
    Process bookmarks from the given file and execute a command for each.
    
    Bookmark data can be passed to the executed command as:
    1. Environment variables (default):
       - BOOKMARK_URL: The URL of the bookmark.
       - BOOKMARK_TITLE: The title of the bookmark.
       - BOOKMARK_PATH_STR: Full folder path as a single string (e.g., "Folder/Subfolder").
       - BOOKMARK_PATH_0, BOOKMARK_PATH_1, ...: Path components (e.g., BOOKMARK_PATH_0="Folder", BOOKMARK_PATH_1="Subfolder").
    2. Command line arguments (if --args is used):
       The URL, Title, and Path components will be appended to the command.
       Example: if --exec "my_script.sh" and a bookmark has path "F1/F2", URL "url", Title "title",
       the command might become: `my_script.sh "url" "title" "F1" "F2"`
    3. Placeholders in the --exec command string:
       - {URL}: Replaced by the bookmark's URL.
       - {TITLE}: Replaced by the bookmark's title.
       - {PATH}: Replaced by the bookmark's full path string.
       These placeholders are processed first.
    """
    
    bookmarks = []
    if input_format == 'html':
        # Assuming parse_html_bookmarks is available
        bookmarks = parse_html_bookmarks(input_file)
    elif input_format == 'json':
        # Assuming parse_json_bookmarks is available
        bookmarks = parse_json_bookmarks(input_file)
    else:
        click.echo(f"Error: Unsupported input format '{input_format}'.", err=True)
        return

    if not bookmarks:
        click.echo("No bookmarks found or an error occurred during parsing.")
        return

    for bookmark in bookmarks:
        url = bookmark.get('url', '')
        title = bookmark.get('title', '')
        path_list = bookmark.get('path', [])
        path_str = path_separator.join(path_list)

        # Prepare environment variables
        current_env = os.environ.copy()
        if env_vars:
            current_env['BOOKMARK_URL'] = url
            current_env['BOOKMARK_TITLE'] = title
            current_env['BOOKMARK_PATH_STR'] = path_str
            for i, part in enumerate(path_list):
                current_env[f'BOOKMARK_PATH_{i}'] = part
        
        # Prepare command with placeholders
        final_command_str = exec_command_str.replace('{URL}', url).replace('{TITLE}', title).replace('{PATH}', path_str)
        
        # Prepare command arguments
        cmd_list = []
        # A more robust way to parse the command string if it has spaces and quotes
        # For now, we'll split by space, which is naive for complex commands.
        # Consider shlex.split for better parsing if this becomes an issue.
        cmd_list.extend(final_command_str.split()) # Basic split, may need shlex for robustness

        if args:
            cmd_list.append(url)
            cmd_list.append(title)
            cmd_list.extend(path_list) # Add path components as separate arguments

        if not cmd_list:
            click.echo("Error: Command to execute is empty after processing.", err=True)
            continue

        click.echo(f"Executing: {' '.join(cmd_list)}")
        click.echo(f"  URL: {url}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Path: {path_str}")
        
        try:
            # Using shell=False is generally safer, but requires cmd_list to be well-formed.
            # If shell=True is needed, ensure final_command_str is carefully constructed to avoid injection.
            # For now, with cmd_list, shell=False is appropriate.
            process_result = subprocess.run(cmd_list, env=current_env, capture_output=True, text=True, check=False)
            if process_result.stdout:
                click.echo(f"  Stdout: {process_result.stdout.strip()}")
            if process_result.stderr:
                click.echo(f"  Stderr: {process_result.stderr.strip()}", err=True)
            if process_result.returncode != 0:
                click.echo(f"  Command exited with error code: {process_result.returncode}", err=True)

        except FileNotFoundError:
            click.echo(f"Error: Command not found: {cmd_list[0]}", err=True)
        except Exception as e:
            click.echo(f"Error executing command '{' '.join(cmd_list)}': {e}", err=True)

if __name__ == '__main__':
    # This is primarily for poetry to run. 
    # If run directly as `python forbookmarks/__main__.py`, ensure parsers are findable.
    main()
