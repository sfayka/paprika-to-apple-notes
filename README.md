# Paprika to Apple Notes Converter

A Python CLI tool that converts Paprika recipe HTML exports to clean, beautifully formatted HTML files ready for import into Apple Notes.

## Features

- **Clean HTML Output**: Converts messy Paprika HTML exports into polished, professional-looking recipe notes
- **Enhanced Formatting**: 
  - Removes leading numbers from recipe titles
  - Standardizes ingredients (fractions, abbreviations, measurements)
  - Breaks instructions into numbered steps
  - Cleans up categories and metadata
- **Modern Styling**: Uses Apple's system fonts and modern CSS for beautiful notes
- **Table of Contents**: Automatically generates a comprehensive recipe index
- **Batch Processing**: Handles thousands of recipes efficiently

## Requirements

- Python 3.7+
- Beautiful Soup 4

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Export your recipes from Paprika**:
   - In Paprika, go to Settings > Export Recipes
   - Choose HTML format
   - Export all recipes to a folder

2. **Run the converter**:
   ```bash
   python paprika_to_apple_notes.py "/path/to/paprika/export/folder" -o "/path/to/output/folder"
   ```

   Example:
   ```bash
   python paprika_to_apple_notes.py "/Users/username/Documents/Recipes from Paprika/Export 2025-03-16 17.31.17 All Recipes/Recipes" -o "apple_notes_recipes"
   ```

3. **Import into Apple Notes**:
   - Open Apple Notes
   - Select or create a folder for your recipes
   - Go to **File > Import to Notes**
   - Select the output folder created by the converter
   - Check "Preserve folder structure on import" if desired
   - Click Import

## What Gets Converted

### Recipe Content
- **Title**: Cleaned and formatted (removes leading numbers, standardizes capitalization)
- **Ingredients**: Standardized measurements and fractions
- **Instructions**: Broken into numbered steps with proper formatting
- **Notes**: Preserved with clean paragraph formatting
- **Source**: Links preserved as clickable URLs
- **Nutrition**: Formatted as clean list items
- **Metadata**: Prep time, cook time, servings, categories

### Table of Contents
- Alphabetically organized recipe index
- Recipe statistics (total count, categories)
- Metadata for each recipe (timing, categories)

## Output Structure

The converter creates:
- Individual HTML files for each recipe (e.g., `Chocolate_Chip_Cookies.html`)
- A table of contents file (`00_Recipe_Collection_Table_of_Contents.html`)
- All files ready for direct import into Apple Notes

## Command Line Options

```bash
python paprika_to_apple_notes.py <source_directory> [options]

Options:
  -o, --output OUTPUT    Output directory (default: ./apple_notes_recipes)
  -h, --help            Show help message
```

## Example Output

The converter transforms raw Paprika HTML into clean, modern recipe notes with:
- Beautiful typography using Apple's system fonts
- Color-coded sections (ingredients, instructions, notes, etc.)
- Responsive design that looks great on all devices
- Professional styling suitable for sharing

## Troubleshooting

- **"No recipes found"**: Make sure you're pointing to the correct Paprika export folder containing .html files
- **Import issues**: Ensure you're using Apple Notes on macOS and selecting "File > Import to Notes"
- **Python errors**: Make sure you've activated the virtual environment and installed dependencies

## Contributing

Feel free to submit issues, feature requests, or improvements via GitHub.

## License

This project is provided as-is for personal use in converting your own recipe collections.