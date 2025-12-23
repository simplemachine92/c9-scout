import requests
import re
from typing import List, Tuple
from bs4 import BeautifulSoup

def print_grid_from_doc(url: str):
    # Grab the doc
    response = requests.get(url)
    response.raise_for_status()
    content = response.text
    
    # Init
    coordinates: List[Tuple[int, int, str]] = []
    
    # Parse html (iterate through <tbody>)
    soup = BeautifulSoup(content, 'html.parser')
    tbody = soup.find(id='tbody')
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 3:
            x = int(cells[0].text)
            y = int(cells[1].text)
            char = cells[2].text
            coordinates.append((x, y, char))

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


if __name__ == "__main__":
    # Run test with sample data
    # test_with_sample_data()
    
    # To use with actual Google Doc:
    example_url = "https://docs.google.com/document/d/e/2PACX-1vTMOmshQe8YvaRXi6gEPKKlsC6UpFJSMAk4mQjLm_u1gmHdVVTaeh7nBNFBRlui0sTZ-snGwZM4DBCT/pub"
    print_grid_from_doc(example_url)