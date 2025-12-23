import requests
import re
from typing import List, Tuple

def print_grid_from_doc(url: str):
    """
    Takes a Google Doc URL containing character coordinates and prints the resulting grid.
    
    The function:
    1. Fetches the Google Doc as plain text
    2. Parses lines in format: x-coordinate | character | y-coordinate
    3. Builds a 2D grid with (0,0) at top-left
    4. Prints the grid showing the secret message
    
    Args:
        url: String containing the URL for the Google Doc with input data
    """
    # Convert Google Doc URL to export format (plain text)
    # Extract the document ID from the URL
    # Handles both /d/ and /e/ URL formats
    doc_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if not doc_id_match:
        # Try /e/ format (published docs)
        doc_id_match = re.search(r'/e/([a-zA-Z0-9-_]+)', url)
    
    if not doc_id_match:
        raise ValueError("Invalid Google Doc URL - could not extract document ID")
    
    doc_id = doc_id_match.group(1)
    
    # For published docs (/e/ format), use the pub endpoint
    if '/e/' in url:
        # Already a published doc, fetch as-is and convert to text export
        export_url = f"https://docs.google.com/document/d/e/{doc_id}/export?format=txt"
    else:
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    
    # Fetch the document content
    response = requests.get(export_url)
    response.raise_for_status()
    content = response.text
    
    # Parse the content to extract coordinates and characters
    coordinates: List[Tuple[int, int, str]] = []
    
    # Split into lines and look for coordinate data
    lines = content.split('\n')
    
    for line in lines:
        # Look for lines that contain coordinate data in format: x-coordinate | character | y-coordinate
        # The line should have pipe separators (tab-separated tables also use |)
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    # Clean and extract parts
                    x_part = parts[0].strip()
                    char_part = parts[1].strip()
                    y_part = parts[2].strip()
                    
                    # Try to parse as integers and character
                    # Skip header rows (common headers: "x-coordinate", "x", "X", etc.)
                    if (x_part.lower() in ['x-coordinate', 'x', 'x coordinate'] or 
                        'coordinate' in x_part.lower()):
                        continue
                    
                    x = int(x_part)
                    y = int(y_part)
                    
                    # The character is in the middle part
                    # Handle multi-character strings by taking the first character
                    if char_part:
                        char = char_part[0] if len(char_part) > 0 else ' '
                        coordinates.append((x, y, char))
                except (ValueError, IndexError):
                    # Skip lines that don't match the expected format
                    continue
    
    if not coordinates:
        print("No valid coordinates found in document")
        return
    
    # Find the dimensions of the grid
    max_x = max(coord[0] for coord in coordinates)
    max_y = max(coord[1] for coord in coordinates)
    
    # Create a 2D grid filled with spaces
    # y increases downward (row 0 is top), x increases rightward (column 0 is left)
    # This matches standard screen coordinates with (0,0) at top-left
    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    
    # Fill in the characters at their specified positions
    for x, y, char in coordinates:
        grid[y][x] = char
    
    # Print the grid row by row
    for row in grid:
        print(''.join(row))


# Test function with sample data
def test_with_sample_data():
    """Test the parsing logic with sample data that forms the letter 'F'"""
    sample_data = """
x-coordinate | character | y-coordinate
0 | █ | 0
1 | ▀ | 0
2 | ▀ | 0
3 | ▀ | 0
0 | █ | 1
1 | ▀ | 1
2 | ▀ | 1
0 | █ | 2
"""
    print("Testing with sample 'F' data:")
    coordinates: List[Tuple[int, int, str]] = []
    
    lines = sample_data.strip().split('\n')
    for line in lines:
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    x_part = parts[0].strip()
                    char_part = parts[1].strip()
                    y_part = parts[2].strip()
                    
                    if 'coordinate' in x_part.lower():
                        continue
                    
                    x = int(x_part)
                    y = int(y_part)
                    if char_part:
                        coordinates.append((x, y, char_part[0]))
                except (ValueError, IndexError):
                    continue
    
    max_x = max(coord[0] for coord in coordinates)
    max_y = max(coord[1] for coord in coordinates)
    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    
    for x, y, char in coordinates:
        grid[y][x] = char
    
    for row in grid:
        print(''.join(row))
    print()


if __name__ == "__main__":
    # Run test with sample data
    test_with_sample_data()
    
    # To use with actual Google Doc:
    # example_url = "https://docs.google.com/document/d/e/2PACX-1vQGUck9HIFCyezsrBSnmENk5ieJuYwpt7YHYEzeNJkIb9OSDdx-ov2nRNReKQyey-cwJOoEKUhLmN9z/pub"
    # print_grid_from_doc(example_url)