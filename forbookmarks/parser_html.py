from bs4 import BeautifulSoup

def parse_html_bookmarks(file_path):
    """
    Parses an HTML bookmarks file and yields bookmark data.

    Args:
        file_path (str): Path to the HTML bookmarks file.

    Yields:
        dict: A dictionary containing 'url' and 'title' for each bookmark.
              Returns an empty dict if parsing fails or no bookmarks are found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    soup = BeautifulSoup(content, 'lxml')

    # Bookmarks are typically <a> tags.
    # A common pattern is that they are often within <DT><A ...> or similar structures.
    # For a simpler first pass, let's find all <a> tags with an href attribute.
    # We will need to be mindful of other <a> tags that are not bookmarks (e.g., in headers/footers if any).
    # Most bookmark files use <DT><H3> for folder names and <DT><A> for bookmarks.
    
    bookmarks_found = False
    for link_tag in soup.find_all('a', href=True):
        url = link_tag.get('href')
        title = link_tag.string
        
        # Basic filtering:
        # - Ensure it's likely a real bookmark (e.g., http/https scheme).
        # - Avoid javascript links or internal anchors if they are not bookmarks.
        if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')):
            bookmarks_found = True
            # For now, folder structure is not extracted, will be added in a future step.
            # To get the folder, one would typically walk up the parse tree
            # or look for preceding <H3> tags within the same <DL><p> structure.
            yield {
                'url': url.strip(),
                'title': title.strip() if title else '',
                'path': [] # Placeholder for folder path
            }
    
    if not bookmarks_found:
        # This helps differentiate between an empty file and a file with no valid bookmark links.
        # Depending on strictness, could raise an error or return a specific signal.
        print(f"Warning: No valid bookmarks found in {file_path}")

if __name__ == '__main__':
    # Example usage for testing the parser directly
    # Create a dummy bookmarks.html file for this to work
    # Test with a sample bookmarks.html:
    sample_html_content = """
    <!DOCTYPE NETSCAPE-Bookmark-file-1>
    <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
    <TITLE>Bookmarks</TITLE>
    <H1>Bookmarks</H1>
    <DL><p>
        <DT><H3 ADD_DATE="1600000000" LAST_MODIFIED="1600000000">Folder 1</H3>
        <DL><p>
            <DT><A HREF="http://example.com/page1" ADD_DATE="1600000001">Example Page 1</A>
            <DT><A HREF="https://example.org/page2" ADD_DATE="1600000002">Example Page 2</A>
        </DL><p>
        <DT><H3 ADD_DATE="1600000000" LAST_MODIFIED="1600000000">Empty Folder</H3>
        <DL><p></DL><p>
        <DT><A HREF="http://another-example.com" ADD_DATE="1600000003">Another Example</A>
    </DL><p>
    """
    with open("bookmarks_sample.html", "w", encoding="utf-8") as f:
        f.write(sample_html_content)

    print("Testing with bookmarks_sample.html:")
    for bm in parse_html_bookmarks("bookmarks_sample.html"):
        print(bm)
    
    # Test with a non-existent file
    print("\nTesting with non_existent_file.html:")
    for bm in parse_html_bookmarks("non_existent_file.html"):
        print(bm) # Should print error and not loop

    # Test with an empty file
    open("empty_bookmarks.html", "w").close()
    print("\nTesting with empty_bookmarks.html:")
    for bm in parse_html_bookmarks("empty_bookmarks.html"):
        print(bm) # Should print warning and not loop
