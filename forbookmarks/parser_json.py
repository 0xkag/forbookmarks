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
    node: JsonNode, path_parts: List[str], browser_type: str
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
    entry_type: str = node.get("type", "")  # Renamed from node_type
    children: List[JsonNode] = node.get("children", [])
    current_path: List[str] = path_parts

    if browser_type == "firefox":
        if entry_type == "text/x-moz-place" and "uri" in node:
            yield {
                "url": str(node["uri"]),
                "title": str(node.get("title", "")),
                "path": path_parts[:],
            }
        elif entry_type == "text/x-moz-place-container" and children:
            folder_name: str = str(node.get("title", "Unnamed Folder"))
            current_path = path_parts + [folder_name]
            for child in children:
                yield from _extract_bookmarks_recursive(
                    child, current_path, browser_type
                )

    elif browser_type == "chrome":
        if entry_type == "url" and "url" in node:
            yield {
                "url": str(node["url"]),
                "title": str(node.get("name", "")),  # Chrome uses 'name'
                "path": path_parts[:],
            }
        elif entry_type == "folder" and children:  # Corrected node_type to entry_type
            folder_name = str(node.get("name", "Unnamed Folder"))
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
        with open(file_path, "r", encoding="utf-8") as file_handler:
            loaded_json_data: JsonNode = json.load(file_handler)  # Renamed from data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return
    except Exception as exception:
        print(f"Error reading file {file_path}: {exception}")
        return

    if "roots" in loaded_json_data and isinstance(
        loaded_json_data["roots"], dict
    ):  # Likely Chrome
        browser_format: str = "chrome"  # Renamed from browser
        roots_dict: Dict[str, JsonNode] = loaded_json_data["roots"]
        for (
            root_name,
            root_node,
        ) in roots_dict.items():  # root_node is e.g. "bookmark_bar" node
            if isinstance(root_node, dict) and "children" in root_node:
                # root_folder_name is e.g. "Bookmarks bar"
                root_folder_name: str = str(root_node.get("name", root_name))
                # Process children of the root_node, starting path with root_folder_name
                for child_entry in root_node.get("children", []):
                    yield from _extract_bookmarks_recursive(
                        child_entry, [root_folder_name], browser_format
                    )
    elif "children" in loaded_json_data and isinstance(
        loaded_json_data["children"], list
    ):  # Likely Firefox
        browser_format = "firefox"  # Renamed from browser
        # Root title in Firefox
        initial_folder_name: str = str(loaded_json_data.get("title", ""))
        initial_path: List[str] = [initial_folder_name] if initial_folder_name else []

        for child_entry in loaded_json_data["children"]:  # Renamed from child_node
            yield from _extract_bookmarks_recursive(
                child_entry, initial_path, browser_format
            )
    else:
        print(f"Warning: Unknown JSON bookmark structure in {file_path}")
        return


if __name__ == "__main__":
    # Create dummy Chrome sample
    CHROME_SAMPLE_DATA: JsonNode = {  # Renamed from CHROME_SAMPLE_CONTENT
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
                                "url": "https://arstechnica.com",
                            }
                        ],
                    },
                ],
                "name": "Bookmarks bar",
                "type": "folder",
            },
            "other": {
                "children": [
                    {
                        "name": "Mozilla",
                        "type": "url",
                        "url": "https://mozilla.org",
                    }
                ],
                "name": "Other Bookmarks",
                "type": "folder",
            },
        },
        "version": 1,
    }
    CHROME_SAMPLE_FILE: str = "chrome_bookmarks_sample.json"  # Renamed
    with open(CHROME_SAMPLE_FILE, "w", encoding="utf-8") as f_out:
        json.dump(CHROME_SAMPLE_DATA, f_out, indent=2)

    # Create dummy Firefox sample
    FIREFOX_SAMPLE_DATA: JsonNode = {  # Renamed from FIREFOX_SAMPLE_CONTENT
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
                "type": "text/x-moz-place-container",  # Folder
                "children": [
                    {
                        "title": "Internal Wiki",
                        "uri": "http://internal.example.com/wiki",
                        "type": "text/x-moz-place",
                    }
                ],
            },
            {
                "title": "A Single Bookmark",
                "uri": "https://single.example.com/",
                "type": "text/x-moz-place",
            },
        ],
    }
    FIREFOX_SAMPLE_FILE: str = "firefox_bookmarks_sample.json"  # Renamed
    with open(FIREFOX_SAMPLE_FILE, "w", encoding="utf-8") as f_out:
        json.dump(FIREFOX_SAMPLE_DATA, f_out, indent=2)

    print(f"Testing with {CHROME_SAMPLE_FILE}:")
    for bookmark in parse_json_bookmarks(CHROME_SAMPLE_FILE):  # Renamed from bm
        print(bookmark)

    print(f"\nTesting with {FIREFOX_SAMPLE_FILE}:")
    for bookmark in parse_json_bookmarks(FIREFOX_SAMPLE_FILE):  # Renamed from bm
        print(bookmark)

    print("\nTesting with non_existent_file.json:")
    for bookmark in parse_json_bookmarks("non_existent_file.json"):  # Renamed from bm
        print(bookmark)

    EMPTY_JSON_FILE: str = "empty_bookmarks.json"  # Renamed
    with open(EMPTY_JSON_FILE, "w", encoding="utf-8") as f_out:
        f_out.write("")  # Invalid JSON
    print(f"\nTesting with {EMPTY_JSON_FILE} (invalid JSON):")
    for bookmark in parse_json_bookmarks(EMPTY_JSON_FILE):  # Renamed from bm
        print(bookmark)

    INVALID_STRUCTURE_FILE: str = "invalid_structure.json"  # Renamed
    with open(INVALID_STRUCTURE_FILE, "w", encoding="utf-8") as f_out:
        json.dump({"foo": "bar"}, f_out)
    print(f"\nTesting with {INVALID_STRUCTURE_FILE} (unknown structure):")
    for bookmark in parse_json_bookmarks(INVALID_STRUCTURE_FILE):  # Renamed from bm
        print(bookmark)
