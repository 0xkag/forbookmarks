# pylint: disable=broad-except, R1732
# R1732: consider-using-with (for open in __main__ block)
"""
HTML Bookmark Parser for forbookmarks.
"""
from typing import Dict, Iterator, List, Union
from bs4 import BeautifulSoup, Tag

# Define a type alias for a bookmark dictionary for clarity
BookmarkData = Dict[str, Union[str, List[str]]]


def parse_html_bookmarks(file_path: str) -> Iterator[BookmarkData]:
    """
    Parses an HTML bookmarks file and yields bookmark data.

    Args:
        file_path (str): Path to the HTML bookmarks file.

    Yields:
        Iterator[BookmarkData]: An iterator of dictionaries,
                                 each containing 'url', 'title', and 'path'.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content: str = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    soup: BeautifulSoup = BeautifulSoup(content, 'lxml')
    bookmarks_found: bool = False

    for link_tag in soup.find_all('a', href=True):
        if not isinstance(link_tag, Tag):
            continue

        url_val: Union[str, List[str], None] = link_tag.get('href')
        title_tag_content: Union[str, Tag, None] = link_tag.string

        url: str
        if isinstance(url_val, list):
            url = url_val[0] if url_val else ""
        elif isinstance(url_val, str):
            url = url_val
        else:
            continue  # Skip if URL is not a string or list of strings

        if not (
            url.startswith('http://') or
            url.startswith('https://') or
            url.startswith('ftp://')
        ):
            continue

        title: str
        if title_tag_content is not None and isinstance(title_tag_content, str):
            title = title_tag_content.strip()
        else:
            title = ''

        bookmarks_found = True
        yield {
            'url': url.strip(),
            'title': title,
            'path': []  # Path extraction not yet in simple HTML parser
        }

    if not bookmarks_found:
        print(f"Warning: No valid bookmarks found in {file_path}")


if __name__ == '__main__':
    # Example usage for testing the parser directly
    # pylint: disable=R1732  # Allow simple open().close() in this test block
    SAMPLE_HTML_CONTENT: str = (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        '<META HTTP-EQUIV="Content-Type" '
        'CONTENT="text/html; charset=UTF-8">\n'
        "<TITLE>Bookmarks</TITLE>\n"
        "<H1>Bookmarks</H1>\n"
        "<DL><p>\n"
        '    <DT><H3 ADD_DATE="1600000000" '
        'LAST_MODIFIED="1600000000">Folder 1</H3>\n'
        "    <DL><p>\n"
        '        <DT><A HREF="http://example.com/page1" '
        'ADD_DATE="1600000001">'
        "Example Page 1</A>\n"
        '        <DT><A HREF="https://example.org/page2" '
        'ADD_DATE="1600000002">'
        "Example Page 2</A>\n"
        "    </DL><p>\n"
        '    <DT><A HREF="http://another-example.com" '
        'ADD_DATE="1600000003">'
        "Another Example</A>\n"
        "</DL><p>\n"
    )
    SAMPLE_FILE_PATH: str = "bookmarks_sample.html"
    with open(SAMPLE_FILE_PATH, "w", encoding="utf-8") as file_handler:
        file_handler.write(SAMPLE_HTML_CONTENT)

    print(f"Testing with {SAMPLE_FILE_PATH}:")
    for bm_data_item in parse_html_bookmarks(SAMPLE_FILE_PATH):
        print(bm_data_item)

    print("\nTesting with non_existent_file.html:")
    for bm_data_item in parse_html_bookmarks("non_existent_file.html"):
        # Should print error and not loop
        print(bm_data_item)

    EMPTY_FILE_PATH: str = "empty_bookmarks.html"
    # The R1732 disable at the top of the file or specifically here might be
    # needed if pylint is very strict about this __main__ block.
    # For a simple script like this, it's minor.
    open(EMPTY_FILE_PATH, "w", encoding="utf-8").close()
    print(f"\nTesting with {EMPTY_FILE_PATH}:")
    for bm_data_item in parse_html_bookmarks(EMPTY_FILE_PATH):
        # Should print warning and not loop
        print(bm_data_item)
