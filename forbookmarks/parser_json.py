import json

def _extract_bookmarks_recursive(node, path_parts, browser_type):
    """
    Recursively extracts bookmarks from a node in the JSON tree.

    Args:
        node (dict): The current node in the JSON bookmark tree.
        path_parts (list): The current folder path.
        browser_type (str): 'chrome' or 'firefox' to handle structural differences.

    Yields:
        dict: A dictionary containing 'url', 'title', and 'path' for each bookmark.
    """
    if browser_type == 'firefox' and 'type' in node:
        if node.get('type') == 'text/x-moz-place' and 'uri' in node: # Bookmark entry
            yield {
                'url': node['uri'],
                'title': node.get('title', ''),
                'path': path_parts[:]
            }
        elif node.get('type') == 'text/x-moz-place-container' and 'children' in node: # Folder
            folder_name = node.get('title', 'Unnamed Folder')
            current_path = path_parts + [folder_name]
            for child in node['children']:
                yield from _extract_bookmarks_recursive(child, current_path, browser_type)
    
    elif browser_type == 'chrome' and 'type' in node:
        if node.get('type') == 'url' and 'url' in node: # Bookmark entry
            yield {
                'url': node['url'],
                'title': node.get('name', ''), # Chrome uses 'name' for title
                'path': path_parts[:]
            }
        elif node.get('type') == 'folder' and 'children' in node: # Folder
            folder_name = node.get('name', 'Unnamed Folder')
            current_path = path_parts + [folder_name]
            for child in node['children']:
                yield from _extract_bookmarks_recursive(child, current_path, browser_type)


def parse_json_bookmarks(file_path):
    """
    Parses a JSON bookmarks file (Chrome or Firefox) and yields bookmark data.

    Args:
        file_path (str): Path to the JSON bookmarks file.

    Yields:
        dict: A dictionary containing 'url', 'title', and 'path' for each bookmark.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    # Detect format (simplified detection)
    # Firefox has a root object, often with a "title" like "Bookmarks Menu" and "children".
    # Chrome has a root object with a "roots" key, which then contains "bookmark_bar", "other", "synced".
    
    if 'roots' in data and isinstance(data['roots'], dict): # Likely Chrome
        browser_type = 'chrome'
        # Chrome bookmarks are typically under 'roots' -> 'bookmark_bar', 'other', etc.
        # We'll iterate through all root folders.
        for root_name, root_node in data['roots'].items():
            if isinstance(root_node, dict) and 'children' in root_node:
                 # The path starts with the name of the root folder (e.g., "Bookmarks bar")
                yield from _extract_bookmarks_recursive(root_node, [root_node.get('name', root_name)], browser_type)
    elif 'children' in data: # Likely Firefox (or a similar structure)
        browser_type = 'firefox'
        # Firefox root often doesn't have a name itself, or it's implicit.
        # The path starts from the children of the root.
        initial_path = [data.get('title', 'Root')] if data.get('title') else []
        for child in data['children']:
            yield from _extract_bookmarks_recursive(child, initial_path, browser_type)
    else:
        print(f"Warning: Unknown JSON bookmark structure in {file_path}")
        return

if __name__ == '__main__':
    # Create dummy Chrome sample
    chrome_sample_content = {
        "checksum": "abcdef123456",
        "roots": {
            "bookmark_bar": {
                "children": [
                    {"name": "Google", "type": "url", "url": "https://google.com"},
                    {
                        "name": "Tech Blogs", "type": "folder", "children": [
                            {"name": "Ars Technica", "type": "url", "url": "https://arstechnica.com"}
                        ]
                    }
                ],
                "name": "Bookmarks bar",
                "type": "folder"
            },
            "other": {
                "children": [
                    {"name": "Mozilla", "type": "url", "url": "https://mozilla.org"}
                ],
                "name": "Other Bookmarks",
                "type": "folder"
            }
        },
        "version": 1
    }
    with open("chrome_bookmarks_sample.json", "w", encoding="utf-8") as f:
        json.dump(chrome_sample_content, f, indent=2)

    # Create dummy Firefox sample
    firefox_sample_content = {
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
                "type": "text/x-moz-place-container", # Folder
                "children": [
                    {
                        "title": "Internal Wiki",
                        "uri": "http://internal.example.com/wiki",
                        "type": "text/x-moz-place"
                    }
                ]
            },
            { # Bookmark directly under root
                "title": "A Single Bookmark",
                "uri": "https://single.example.com/",
                "type": "text/x-moz-place"
            }
        ]
    }
    with open("firefox_bookmarks_sample.json", "w", encoding="utf-8") as f:
        json.dump(firefox_sample_content, f, indent=2)

    print("Testing with chrome_bookmarks_sample.json:")
    for bm in parse_json_bookmarks("chrome_bookmarks_sample.json"):
        print(bm)

    print("\nTesting with firefox_bookmarks_sample.json:")
    for bm in parse_json_bookmarks("firefox_bookmarks_sample.json"):
        print(bm)

    print("\nTesting with non_existent_file.json:")
    for bm in parse_json_bookmarks("non_existent_file.json"):
        print(bm)

    open("empty_bookmarks.json", "w").close()
    print("\nTesting with empty_bookmarks.json (invalid JSON):")
    for bm in parse_json_bookmarks("empty_bookmarks.json"):
        print(bm)
        
    with open("invalid_structure.json", "w", encoding="utf-8") as f:
        json.dump({"foo": "bar"}, f)
    print("\nTesting with invalid_structure.json (unknown structure):")
    for bm in parse_json_bookmarks("invalid_structure.json"):
        print(bm)
