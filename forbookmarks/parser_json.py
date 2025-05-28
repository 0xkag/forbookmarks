# pylint: disable=broad-except
"""
JSON Bookmark Parser for forbookmarks.
Handles Chrome and Firefox JSON bookmark structures.
"""
import json
from typing import Any, Dict, Iterator, List, Union

# Define a type alias for a bookmark dictionary for clarity
BookmarkData = Dict[str, Union[str, List[str]]]
# Type for a node in the JSON bookmark tree
JsonNode = Dict[str, Any]


def _extract_bookmarks_recursive(
    node: JsonNode,
    path_parts: List[str],
    browser_type: str
) -> Iterator[BookmarkData]:
    """
    Recursively extracts bookmarks from a node in the JSON tree.

    Args:
        node (JsonNode): The current node in the JSON bookmark tree.
        path_parts (List[str]): The current folder path.
        browser_type (str): 'chrome' or 'firefox' to handle structure.

    Yields:
        Iterator[BookmarkData]: Bookmark data dictionaries.
    """
    node_type: str = node.get('type', '')
    children: List[JsonNode] = node.get('children', [])
    current_path: List[str] = path_parts

    if browser_type == 'firefox':
        if node_type == 'text/x-moz-place' and 'uri' in node:
            yield {
                'url': str(node['uri']),
                'title': str(node.get('title', '')),
                'path': path_parts[:]
            }
        elif node_type == 'text/x-moz-place-container' and children:
            folder_name: str = str(node.get('title', 'Unnamed Folder'))
            current_path = path_parts + [folder_name]
            for child in children:
                yield from _extract_bookmarks_recursive(child, current_path, browser_type)

    elif browser_type == 'chrome':
        if node_type == 'url' and 'url' in node:
            yield {
                'url': str(node['url']),
                'title': str(node.get('name', '')),  # Chrome uses 'name'
                'path': path_parts[:]
            }
        elif node_type == 'folder' and children:
            folder_name = str(node.get('name', 'Unnamed Folder'))
            current_path = path_parts + [folder_name]
            for child in children:
                yield from _extract_bookmarks_recursive(
                    child, current_path, browser_type
                )


def parse_json_bookmarks(file_path: str) -> Iterator[BookmarkData]:
    """
    Parses a JSON bookmarks file (Chrome or Firefox) and yields bookmark data.

    Args:
        file_path (str): Path to the JSON bookmarks file.

    Yields:
        Iterator[BookmarkData]: Bookmark data dictionaries.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data: JsonNode = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    if 'roots' in data and isinstance(data['roots'], dict):  # Likely Chrome
        browser: str = 'chrome'
        roots_dict: Dict[str, JsonNode] = data['roots']
        for root_name, root_node in roots_dict.items():
            if isinstance(root_node, dict) and 'children' in root_node:
                folder_name: str = str(root_node.get('name', root_name))
                yield from _extract_bookmarks_recursive(
                    root_node, [folder_name], browser
                )
    elif 'children' in data and isinstance(data['children'], list):  # Likely Firefox
        browser = 'firefox'
        # Root title in Firefox (can be empty)
        initial_folder_name: str = str(data.get('title', ''))
        # If root title is empty, path starts empty, else with root title
        initial_path: List[str] = \
            [initial_folder_name] if initial_folder_name else []

        for child_node in data['children']:
            yield from _extract_bookmarks_recursive(
                child_node, initial_path, browser
            )
    else:
        print(f"Warning: Unknown JSON bookmark structure in {file_path}")
        return


if __name__ == '__main__':
    # Create dummy Chrome sample
    CHROME_SAMPLE_CONTENT: JsonNode = {
        "checksum": "abcdef123456",
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
                                "url": "https://arstechnica.com"
                            }
                        ]
                    }
                ],
                "name": "Bookmarks bar",
                "type": "folder"
            },
            "other": {
                "children": [
                    {
                        "name": "Mozilla",
                        "type": "url",
                        "url": "https://mozilla.org"
                    }
                ],
                "name": "Other Bookmarks",
                "type": "folder"
            }
        },
        "version": 1
    }
    CHROME_SAMPLE_PATH: str = "chrome_bookmarks_sample.json"
    with open(CHROME_SAMPLE_PATH, "w", encoding="utf-8") as f_out:
        json.dump(CHROME_SAMPLE_CONTENT, f_out, indent=2)

    # Create dummy Firefox sample
    FIREFOX_SAMPLE_CONTENT: JsonNode = {
        "title": "Bookmarks Menu",
        "root": "placesRoot",
        "children": [
            {
                "title": "Mozilla Firefox",
                "uri": "https://www.mozilla.org/firefox/",
                "type": "text/x-moz-place"
            },
            {
                "title": "Work Stuff",
                "type": "text/x-moz-place-container",  # Folder
                "children": [
                    {
                        "title": "Internal Wiki",
                        "uri": "http://internal.example.com/wiki",
                        "type": "text/x-moz-place"
                    }
                ]
            },
            {
                "title": "A Single Bookmark",
                "uri": "https://single.example.com/",
                "type": "text/x-moz-place"
            }
        ]
    }
    FIREFOX_SAMPLE_PATH: str = "firefox_bookmarks_sample.json"
    with open(FIREFOX_SAMPLE_PATH, "w", encoding="utf-8") as f_out:
        json.dump(FIREFOX_SAMPLE_CONTENT, f_out, indent=2)

    print(f"Testing with {CHROME_SAMPLE_PATH}:")
    for bm in parse_json_bookmarks(CHROME_SAMPLE_PATH):
        print(bm)

    print(f"\nTesting with {FIREFOX_SAMPLE_PATH}:")
    for bm in parse_json_bookmarks(FIREFOX_SAMPLE_PATH):
        print(bm)

    print("\nTesting with non_existent_file.json:")
    for bm in parse_json_bookmarks("non_existent_file.json"):
        print(bm)

    EMPTY_JSON_PATH: str = "empty_bookmarks.json"
    with open(EMPTY_JSON_PATH, "w", encoding="utf-8") as f_out:
        f_out.write("")  # Invalid JSON
    print(f"\nTesting with {EMPTY_JSON_PATH} (invalid JSON):")
    for bm in parse_json_bookmarks(EMPTY_JSON_PATH):
        print(bm)

    INVALID_STRUCTURE_PATH: str = "invalid_structure.json"
    with open(INVALID_STRUCTURE_PATH, "w", encoding="utf-8") as f_out:
        json.dump({"foo": "bar"}, f_out)
    print(f"\nTesting with {INVALID_STRUCTURE_PATH} (unknown structure):")
    for bm in parse_json_bookmarks(INVALID_STRUCTURE_PATH):
        print(bm)
