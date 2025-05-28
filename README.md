# forbookmarks

`forbookmarks` is a command-line tool inspired by `formail` (from the `procmail` package), but designed to work with web browser bookmark files. It allows you to iterate over bookmarks from Chrome or Firefox (exported as HTML or JSON backup files) and execute a command for each bookmark.

## Features

*   Parses HTML bookmark files (Netscape Bookmark File Format).
*   Parses JSON bookmark backup files from Chrome and Firefox.
*   Executes a user-defined command for each bookmark.
*   Passes bookmark information (URL, title, folder path) to the command via:
    *   Environment variables (default).
    *   Placeholders in the command string (`{URL}`, `{TITLE}`, `{PATH}`).
    *   Command-line arguments.

## Requirements

*   Python 3.11+
*   Poetry for dependency management and installation.

## Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd forbookmarks 
    ```
    *(Replace `<repository_url>` with the actual URL of this project's repository if applicable, otherwise this step is for users who clone it manually)*

2.  **Install using Poetry:**
    Poetry will handle the creation of a virtual environment and installation of dependencies.
    ```bash
    poetry install
    ```

## Usage

The main command is `process`. You need to specify the input bookmark file, its format, and the command to execute.

```bash
poetry run forbookmarks process [OPTIONS]
```

### Options for `process` command:

*   `-f, --input-file PATH`: Path to the bookmarks file. (Required)
*   `-i, --input-format [html|json]`: Format of the bookmarks file. (Required)
*   `-x, --exec TEXT`: Command to execute for each bookmark. (Required)
*   `--env-vars / --no-env-vars`: Pass bookmark data as environment variables (BOOKMARK_URL, BOOKMARK_TITLE, BOOKMARK_PATH_STR, BOOKMARK_PATH_0, ...). (Default: `--env-vars`)
*   `--args / --no-args`: Pass bookmark data as command line arguments to the executed command. (Default: `--no-args`)
*   `--path-separator TEXT`: Separator for joining folder path elements in BOOKMARK_PATH_STR or for command line arguments. (Default: `/`)
*   `--help`: Show help message and exit.

### How Bookmark Data is Passed to Commands:

1.  **Environment Variables (default, with `--env-vars`):**
    *   `BOOKMARK_URL`: The URL of the bookmark.
    *   `BOOKMARK_TITLE`: The title of the bookmark.
    *   `BOOKMARK_PATH_STR`: Full folder path as a single string (e.g., "Folder/Subfolder").
    *   `BOOKMARK_PATH_0`, `BOOKMARK_PATH_1`, ...: Individual path components (e.g., `BOOKMARK_PATH_0="Folder"`, `BOOKMARK_PATH_1="Subfolder"`).

2.  **Placeholders in Command String:**
    You can use these placeholders directly in your `--exec` command:
    *   `{URL}`: Replaced by the bookmark's URL.
    *   `{TITLE}`: Replaced by the bookmark's title.
    *   `{PATH}`: Replaced by the bookmark's full path string (joined by `--path-separator`).
    These are processed before environment variables or arguments are set up for the subprocess.

3.  **Command Line Arguments (with `--args`):**
    If `--args` is specified, the following are appended to your command, in order:
    *   URL
    *   Title
    *   Each component of the folder path as a separate argument.

### Examples:

1.  **Echo bookmark details from an HTML file:**
    ```bash
    poetry run forbookmarks process -f bookmarks.html -i html -x "echo URL: {URL}, Title: {TITLE}, Path: {PATH}"
    ```

2.  **Process a JSON backup and use environment variables with a custom script:**
    Assume `my_script.sh` uses `BOOKMARK_URL` and `BOOKMARK_TITLE`:
    ```bash
    # my_script.sh content:
    # #!/bin/sh
    # echo "Processing $BOOKMARK_TITLE at $BOOKMARK_URL from folder $BOOKMARK_PATH_STR"

    poetry run forbookmarks process -f chrome_bookmarks.json -i json -x "./my_script.sh"
    ```

3.  **Pass data as arguments to a script from a Firefox JSON backup:**
    ```bash
    # another_script.py content:
    # import sys
    # print(f"URL: {sys.argv[1]}, Title: {sys.argv[2]}, Path: {'/'.join(sys.argv[3:])}")
    
    poetry run forbookmarks process -f firefox_bookmarks.json -i json -x "python another_script.py" --args --no-env-vars
    ```

## Development

To run tests:
```bash
poetry run python -m unittest discover tests
```

Or, if you prefer `pytest` (you'd need to add it to dev dependencies in `pyproject.toml`):
```bash
poetry add pytest --group dev
poetry run pytest
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.
*(Further details can be added here as the project evolves)*

## License

*(Specify License Here - e.g., MIT, Apache 2.0. For now, leaving as a placeholder)*
This project is unlicensed (or specify your chosen license).
```
