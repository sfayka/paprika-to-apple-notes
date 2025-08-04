#!/usr/bin/env python3
"""
Paprika to Apple Notes Converter

Converts Paprika recipe HTML exports to clean HTML format suitable for Apple Notes import.
Creates individual note files for each recipe plus a table of contents.
"""

import os
import re
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import shutil
from typing import List, Dict, Optional
import html
import unicodedata


class Recipe:
    """Represents a single recipe with all its components."""
    
    def __init__(self, html_file: Path):
        self.source_file = html_file
        self.title = ""
        self.categories = []
        self.prep_time = ""
        self.cook_time = ""
        self.servings = ""
        self.source_url = ""
        self.source_name = ""
        self.ingredients = []
        self.instructions = ""
        self.notes = ""
        self.nutrition = ""
        self.image_path = ""
        
        self._parse_html()
    
    def _parse_html(self):
        """Parse the Paprika HTML file and extract recipe data."""
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', {'itemprop': 'name'})
            if title_elem:
                self.title = self._clean_title(title_elem.get_text().strip())
            
            # Extract categories
            categories_elem = soup.find('p', {'itemprop': 'recipeCategory'})
            if categories_elem:
                categories_text = categories_elem.get_text().strip()
                self.categories = [self._clean_category(cat.strip()) for cat in categories_text.split(',') if cat.strip()]
            
            # Extract timing information
            prep_elem = soup.find('span', {'itemprop': 'prepTime'})
            if prep_elem:
                self.prep_time = self._clean_time(prep_elem.get_text().strip())
                
            cook_elem = soup.find('span', {'itemprop': 'cookTime'})
            if cook_elem:
                self.cook_time = self._clean_time(cook_elem.get_text().strip())
                
            servings_elem = soup.find('span', {'itemprop': 'recipeYield'})
            if servings_elem:
                self.servings = self._clean_servings(servings_elem.get_text().strip())
            
            # Extract source information
            source_elem = soup.find('a', {'itemprop': 'url'})
            if source_elem:
                self.source_url = source_elem.get('href', '').strip()
                author_elem = source_elem.find('span', {'itemprop': 'author'})
                if author_elem:
                    self.source_name = self._clean_text(author_elem.get_text().strip())
            
            # Extract ingredients
            ingredient_elems = soup.find_all('p', {'itemprop': 'recipeIngredient'})
            for elem in ingredient_elems:
                ingredient_text = self._clean_ingredient(elem.get_text().strip())
                if ingredient_text:
                    self.ingredients.append(ingredient_text)
            
            # Extract instructions
            instructions_elem = soup.find('div', {'itemprop': 'recipeInstructions'})
            if instructions_elem:
                # Get the raw HTML to preserve line breaks
                instructions_html = str(instructions_elem)
                self.instructions = self._clean_instructions(instructions_html)
            
            # Extract notes
            notes_elem = soup.find('div', {'itemprop': 'comment'})
            if notes_elem:
                notes_html = str(notes_elem)
                self.notes = self._clean_notes(notes_html)
            
            # Extract nutrition
            nutrition_elem = soup.find('div', {'itemprop': 'nutrition'})
            if nutrition_elem:
                nutrition_html = str(nutrition_elem)
                self.nutrition = self._clean_nutrition(nutrition_html)
            
            # Extract image path
            img_elem = soup.find('img', {'itemprop': 'image'})
            if img_elem:
                self.image_path = img_elem.get('src', '')
                
        except Exception as e:
            print(f"Error parsing {self.source_file}: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _clean_title(self, title: str) -> str:
        """Clean and standardize recipe titles."""
        title = self._clean_text(title)
        
        if not title:
            return "Untitled Recipe"
        
        # Remove leading numbers and dots (e.g., "1.", "20.", etc.)
        title = re.sub(r'^\d+\.\s*', '', title)
        
        # Remove common prefixes that might be inconsistent
        title = re.sub(r'^(Recipe:\s*|RECIPE:\s*)', '', title, flags=re.IGNORECASE)
        
        # Clean up all-caps titles (convert to title case if more than 70% is uppercase)
        if len([c for c in title if c.isupper()]) > len(title) * 0.7 and len(title) > 3:
            # Split on common separators and title case each part
            parts = re.split(r'(\s+(?:with|and|&|in|on|for|or)\s+)', title, flags=re.IGNORECASE)
            title_parts = []
            for part in parts:
                if re.match(r'\s+(?:with|and|&|in|on|for|or)\s+', part, re.IGNORECASE):
                    title_parts.append(part.lower())
                else:
                    title_parts.append(part.title())
            title = ''.join(title_parts)
        
        # Fix common title formatting issues
        title = re.sub(r'\s+', ' ', title)  # Multiple spaces
        title = title.strip()
        
        return title
    
    def _clean_category(self, category: str) -> str:
        """Clean and standardize category names."""
        category = self._clean_text(category)
        
        # Standardize common category names
        category_mapping = {
            'air fryer': 'Air Fryer',
            'crockpot': 'Crockpot',
            'slow cooker': 'Slow Cooker',
            'instant pot': 'Instant Pot',
            'pressure cooker': 'Pressure Cooker',
            'oven': 'Oven',
            'stove': 'Stovetop',
            'grill': 'Grilled',
            'no bake': 'No Bake',
            'vegetarian': 'Vegetarian',
            'vegan': 'Vegan',
            'keto': 'Keto',
            'low carb': 'Low Carb',
            'gluten free': 'Gluten Free',
            'dairy free': 'Dairy Free'
        }
        
        category_lower = category.lower()
        for key, value in category_mapping.items():
            if key in category_lower:
                category = value
                break
        else:
            # Title case if not found in mapping
            category = category.title()
        
        return category
    
    def _clean_time(self, time_str: str) -> str:
        """Clean and standardize time values."""
        time_str = self._clean_text(time_str)
        
        if not time_str:
            return ""
        
        # Standardize time formats - be more careful about word boundaries
        time_str = re.sub(r'(\d+)\s*mins?\b', r'\1 minutes', time_str, flags=re.IGNORECASE)
        time_str = re.sub(r'(\d+)\s*hrs?\b', r'\1 hours', time_str, flags=re.IGNORECASE)
        time_str = re.sub(r'(\d+)\s*h\s*(\d+)\s*m\b', r'\1 hours \2 minutes', time_str, flags=re.IGNORECASE)
        
        # Handle cases where "minutes" might already be there to avoid duplication
        time_str = re.sub(r'(\d+)\s+minutesutes', r'\1 minutes', time_str, flags=re.IGNORECASE)
        time_str = re.sub(r'(\d+)\s+hoursours', r'\1 hours', time_str, flags=re.IGNORECASE)
        
        return time_str
    
    def _clean_servings(self, servings: str) -> str:
        """Clean and standardize serving information."""
        servings = self._clean_text(servings)
        
        # Remove "Yield:" prefix if present
        servings = re.sub(r'^(Yield:\s*|Serves:\s*)', '', servings, flags=re.IGNORECASE)
        
        return servings
    
    def _clean_ingredient(self, ingredient: str) -> str:
        """Clean and standardize ingredient formatting."""
        ingredient = self._clean_text(ingredient)
        
        if not ingredient:
            return ""
        
        # Standardize fractions
        fraction_map = {
            '½': '1/2', '⅓': '1/3', '⅔': '2/3', '¼': '1/4', '¾': '3/4',
            '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5', '⅙': '1/6',
            '⅚': '5/6', '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8'
        }
        
        for unicode_frac, ascii_frac in fraction_map.items():
            ingredient = ingredient.replace(unicode_frac, ascii_frac)
        
        # Standardize common abbreviations
        abbrev_map = {
            r'\bT\b': 'tbsp', r'\btsp\b': 'tsp', r'\btbsp\b': 'tbsp',
            r'\bc\b': 'cup', r'\bC\b': 'cup', r'\bcups?\b': 'cup',
            r'\blb\b': 'lb', r'\blbs\b': 'lb', r'\bpounds?\b': 'lb',
            r'\boz\b': 'oz', r'\bounces?\b': 'oz',
            r'\bpkg\b': 'package', r'\bpkgs\b': 'package'
        }
        
        for pattern, replacement in abbrev_map.items():
            ingredient = re.sub(pattern, replacement, ingredient, flags=re.IGNORECASE)
        
        return ingredient
    
    def _clean_instructions(self, instructions_html: str) -> List[str]:
        """Clean and format instructions into proper steps."""
        if not instructions_html:
            return []
        
        # Parse HTML to extract text while preserving structure
        soup = BeautifulSoup(instructions_html, 'html.parser')
        text = soup.get_text()
        text = self._clean_text(text)
        
        # Split into steps - try multiple delimiters
        steps = []
        
        # First try splitting on <br/> if present in original
        if '<br/>' in instructions_html.lower():
            raw_steps = re.split(r'<br\s*/?>', instructions_html, flags=re.IGNORECASE)
            for step in raw_steps:
                step_soup = BeautifulSoup(step, 'html.parser')
                step_text = self._clean_text(step_soup.get_text())
                if step_text:
                    steps.append(step_text)
        else:
            # Try splitting on sentence endings followed by capital letters
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
            current_step = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # If sentence starts with cooking action words, it's likely a new step
                action_words = r'^(heat|cook|add|mix|stir|combine|bake|fry|grill|roast|simmer|boil|sauté|season|serve|remove|place|put|set|preheat|prepare|cut|chop|slice|dice|mince)'
                
                if re.match(action_words, sentence, re.IGNORECASE) and current_step:
                    steps.append(current_step.strip())
                    current_step = sentence
                else:
                    if current_step:
                        current_step += " " + sentence
                    else:
                        current_step = sentence
            
            if current_step:
                steps.append(current_step.strip())
        
        # Clean up each step
        cleaned_steps = []
        for i, step in enumerate(steps, 1):
            step = step.strip()
            if not step:
                continue
            
            # Remove step numbers if present
            step = re.sub(r'^\d+\.\s*', '', step)
            
            # Ensure step ends with proper punctuation
            if step and not step[-1] in '.!?':
                step += '.'
            
            cleaned_steps.append(step)
        
        return cleaned_steps
    
    def _clean_notes(self, notes_html: str) -> List[str]:
        """Clean and format notes into paragraphs."""
        if not notes_html:
            return []
        
        soup = BeautifulSoup(notes_html, 'html.parser')
        
        # Handle paragraph tags
        paragraphs = soup.find_all('p')
        if paragraphs:
            notes = []
            for p in paragraphs:
                note_text = self._clean_text(p.get_text())
                if note_text:
                    notes.append(note_text)
            return notes
        else:
            # Fallback to splitting by line breaks
            text = soup.get_text()
            text = self._clean_text(text)
            if text:
                # Split on double line breaks or other paragraph indicators
                notes = re.split(r'\n\s*\n|\. {2,}', text)
                return [self._clean_text(note) for note in notes if self._clean_text(note)]
            return []
    
    def _clean_nutrition(self, nutrition_html: str) -> List[str]:
        """Clean and format nutrition information."""
        if not nutrition_html:
            return []
        
        soup = BeautifulSoup(nutrition_html, 'html.parser')
        text = soup.get_text()
        text = self._clean_text(text)
        
        if not text:
            return []
        
        # Split nutrition info by line breaks or common delimiters
        nutrition_items = re.split(r'<br\s*/?>', nutrition_html, flags=re.IGNORECASE)
        if len(nutrition_items) == 1:
            # Try other delimiters
            nutrition_items = re.split(r'[,;]|\n', text)
        
        cleaned_items = []
        for item in nutrition_items:
            soup_item = BeautifulSoup(item, 'html.parser') if '<' in item else None
            item_text = soup_item.get_text() if soup_item else item
            item_text = self._clean_text(item_text)
            
            if item_text and ':' in item_text:
                # Format nutrition items consistently
                parts = item_text.split(':', 1)
                if len(parts) == 2:
                    label = parts[0].strip().title()
                    value = parts[1].strip()
                    cleaned_items.append(f"{label}: {value}")
        
        return cleaned_items
    
    def to_clean_html(self) -> str:
        """Convert recipe to clean HTML format suitable for Apple Notes."""
        html_parts = []
        
        # Start HTML document
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html><head><meta charset="UTF-8">')
        html_parts.append('<title>' + self._escape_html(self.title) + '</title>')
        html_parts.append('<style>')
        html_parts.append('body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; line-height: 1.6; color: #1d1d1f; }')
        html_parts.append('h1 { color: #1d1d1f; border-bottom: 3px solid #007aff; padding-bottom: 12px; margin-bottom: 20px; font-size: 28px; }')
        html_parts.append('h2 { color: #007aff; margin-top: 30px; margin-bottom: 15px; font-size: 20px; font-weight: 600; }')
        html_parts.append('.metadata { background: linear-gradient(135deg, #f5f5f7 0%, #e8e8ea 100%); padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #007aff; }')
        html_parts.append('.metadata p { margin: 8px 0; }')
        html_parts.append('.metadata strong { color: #1d1d1f; }')
        html_parts.append('.ingredients { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #0ea5e9; }')
        html_parts.append('.instructions { margin: 20px 0; }')
        html_parts.append('.instructions ol { padding-left: 0; counter-reset: step-counter; }')
        html_parts.append('.instructions li { list-style: none; counter-increment: step-counter; margin-bottom: 15px; padding: 15px; background-color: #fafafa; border-radius: 8px; border-left: 4px solid #10b981; position: relative; }')
        html_parts.append('.instructions li::before { content: counter(step-counter); position: absolute; left: -25px; top: 15px; background: #10b981; color: white; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; }')
        html_parts.append('.notes { background: linear-gradient(135deg, #fffbf0 0%, #fef3c7 100%); padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #f59e0b; }')
        html_parts.append('.nutrition { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #22c55e; }')
        html_parts.append('ul { padding-left: 20px; }')
        html_parts.append('li { margin-bottom: 8px; }')
        html_parts.append('a { color: #007aff; text-decoration: none; }')
        html_parts.append('a:hover { text-decoration: underline; }')
        html_parts.append('.source { margin: 25px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #6c757d; }')
        html_parts.append('</style>')
        html_parts.append('</head><body>')
        
        # Title
        html_parts.append(f'<h1>{self._escape_html(self.title)}</h1>')
        
        # Metadata section
        if any([self.prep_time, self.cook_time, self.servings, self.categories]):
            html_parts.append('<div class="metadata">')
            metadata_items = []
            if self.prep_time:
                metadata_items.append(f'<p><strong>Prep Time:</strong> {self._escape_html(self.prep_time)}</p>')
            if self.cook_time:
                metadata_items.append(f'<p><strong>Cook Time:</strong> {self._escape_html(self.cook_time)}</p>')
            if self.servings:
                metadata_items.append(f'<p><strong>Servings:</strong> {self._escape_html(self.servings)}</p>')
            if self.categories:
                categories_str = ", ".join(self._escape_html(cat) for cat in self.categories)
                metadata_items.append(f'<p><strong>Categories:</strong> {categories_str}</p>')
            
            html_parts.extend(metadata_items)
            html_parts.append('</div>')
        
        # Ingredients
        if self.ingredients:
            html_parts.append('<div class="ingredients">')
            html_parts.append('<h2>Ingredients</h2>')
            html_parts.append('<ul>')
            for ingredient in self.ingredients:
                html_parts.append(f'<li>{self._escape_html(ingredient)}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Instructions
        if self.instructions:
            html_parts.append('<h2>Instructions</h2>')
            html_parts.append('<div class="instructions">')
            html_parts.append('<ol>')
            for step in self.instructions:
                html_parts.append(f'<li>{self._escape_html(step)}</li>')
            html_parts.append('</ol>')
            html_parts.append('</div>')
        
        # Notes
        if self.notes:
            html_parts.append('<div class="notes">')
            html_parts.append('<h2>Notes</h2>')
            for note in self.notes:
                html_parts.append(f'<p>{self._escape_html(note)}</p>')
            html_parts.append('</div>')
        
        # Source
        if self.source_name or self.source_url:
            html_parts.append('<div class="source">')
            html_parts.append('<h2>Source</h2>')
            if self.source_url:
                source_text = self.source_name or self.source_url
                html_parts.append(f'<p><a href="{self._escape_html(self.source_url)}" target="_blank">{self._escape_html(source_text)}</a></p>')
            else:
                html_parts.append(f'<p>{self._escape_html(self.source_name)}</p>')
            html_parts.append('</div>')
        
        # Nutrition
        if self.nutrition:
            html_parts.append('<div class="nutrition">')
            html_parts.append('<h2>Nutrition Information</h2>')
            for nutrition_item in self.nutrition:
                html_parts.append(f'<p>{self._escape_html(nutrition_item)}</p>')
            html_parts.append('</div>')
        
        # End HTML document
        html_parts.append('</body></html>')
        
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))


class PaprikaToAppleNotesConverter:
    """Main converter class."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.recipes: List[Recipe] = []
    
    def convert(self):
        """Main conversion process."""
        print(f"Converting recipes from {self.source_dir} to {self.output_dir}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find and parse all recipe HTML files
        self._find_recipes()
        
        # Convert each recipe
        self._convert_recipes()
        
        # Create table of contents
        self._create_table_of_contents()
        
        print(f"\nConversion complete!")
        print(f"Generated {len(self.recipes)} recipe files in {self.output_dir}")
        print(f"To import into Apple Notes:")
        print(f"1. Open Apple Notes")
        print(f"2. Select a folder or create a new one")
        print(f"3. Go to File > Import to Notes")
        print(f"4. Select the folder: {self.output_dir}")
        print(f"5. Check 'Preserve folder structure on import' if desired")
    
    def _find_recipes(self):
        """Find all recipe HTML files in the source directory."""
        print("Finding recipe files...")
        
        html_files = list(self.source_dir.rglob("*.html"))
        
        # Filter out index.html and other non-recipe files
        recipe_files = [f for f in html_files if f.name.lower() != 'index.html']
        
        print(f"Found {len(recipe_files)} recipe files")
        
        for html_file in recipe_files:
            try:
                recipe = Recipe(html_file)
                if recipe.title:  # Only add if we successfully parsed a title
                    self.recipes.append(recipe)
                else:
                    print(f"Warning: Could not parse title from {html_file.name}")
            except Exception as e:
                print(f"Error processing {html_file.name}: {e}")
        
        print(f"Successfully parsed {len(self.recipes)} recipes")
    
    def _convert_recipes(self):
        """Convert all recipes to clean HTML format."""
        print("Converting recipes to Apple Notes format...")
        
        for i, recipe in enumerate(self.recipes, 1):
            try:
                # Create safe filename
                safe_filename = self._make_safe_filename(recipe.title)
                output_file = self.output_dir / f"{safe_filename}.html"
                
                # Write clean HTML
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(recipe.to_clean_html())
                
                if i % 50 == 0:  # Progress update every 50 recipes
                    print(f"Converted {i}/{len(self.recipes)} recipes...")
                    
            except Exception as e:
                print(f"Error converting {recipe.title}: {e}")
    
    def _create_table_of_contents(self):
        """Create a table of contents HTML file."""
        print("Creating table of contents...")
        
        # Sort recipes by title
        sorted_recipes = sorted(self.recipes, key=lambda r: r.title.lower())
        
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html><head><meta charset="UTF-8">')
        html_parts.append('<title>Recipe Collection - Table of Contents</title>')
        html_parts.append('<style>')
        html_parts.append('body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }')
        html_parts.append('h1 { color: #1d1d1f; border-bottom: 2px solid #007aff; padding-bottom: 10px; }')
        html_parts.append('h2 { color: #007aff; margin-top: 25px; }')
        html_parts.append('.recipe-list { columns: 2; column-gap: 30px; }')
        html_parts.append('.recipe-item { break-inside: avoid; margin-bottom: 15px; padding: 10px; background-color: #f5f5f7; border-radius: 8px; }')
        html_parts.append('.recipe-title { font-weight: bold; font-size: 16px; margin-bottom: 5px; }')
        html_parts.append('.recipe-meta { font-size: 14px; color: #666; }')
        html_parts.append('.stats { background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0; }')
        html_parts.append('</style>')
        html_parts.append('</head><body>')
        
        html_parts.append('<h1>Recipe Collection</h1>')
        
        # Statistics
        total_recipes = len(sorted_recipes)
        categories = set()
        for recipe in sorted_recipes:
            categories.update(recipe.categories)
        
        html_parts.append('<div class="stats">')
        html_parts.append(f'<p><strong>Total Recipes:</strong> {total_recipes}</p>')
        html_parts.append(f'<p><strong>Categories:</strong> {len(categories)}</p>')
        html_parts.append('</div>')
        
        # Group recipes by first letter
        current_letter = ""
        html_parts.append('<div class="recipe-list">')
        
        for recipe in sorted_recipes:
            first_letter = recipe.title[0].upper() if recipe.title else '#'
            
            if first_letter != current_letter:
                if current_letter:  # Close previous section
                    html_parts.append('</div>')
                current_letter = first_letter
                html_parts.append(f'<h2>{current_letter}</h2>')
            
            html_parts.append('<div class="recipe-item">')
            html_parts.append(f'<div class="recipe-title">{recipe._escape_html(recipe.title)}</div>')
            
            meta_parts = []
            if recipe.categories:
                meta_parts.append(f"Categories: {', '.join(recipe.categories)}")
            if recipe.prep_time:
                meta_parts.append(f"Prep: {recipe.prep_time}")
            if recipe.cook_time:
                meta_parts.append(f"Cook: {recipe.cook_time}")
            
            if meta_parts:
                html_parts.append(f'<div class="recipe-meta">{" • ".join(meta_parts)}</div>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        html_parts.append('</body></html>')
        
        # Write table of contents
        toc_file = self.output_dir / "00_Recipe_Collection_Table_of_Contents.html"
        with open(toc_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))
    
    def _make_safe_filename(self, title: str) -> str:
        """Create a safe filename from recipe title."""
        # Remove or replace problematic characters
        safe = re.sub(r'[<>:"/\\|?*]', '', title)
        safe = re.sub(r'[&]', 'and', safe)
        safe = re.sub(r'\s+', '_', safe.strip())
        
        # Limit length
        if len(safe) > 100:
            safe = safe[:100]
        
        return safe or "untitled_recipe"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Convert Paprika recipe exports to Apple Notes format')
    parser.add_argument('source_dir', 
                       help='Path to Paprika recipe export directory')
    parser.add_argument('-o', '--output', 
                       default='./apple_notes_recipes',
                       help='Output directory for converted files (default: ./apple_notes_recipes)')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output)
    
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist")
        return 1
    
    converter = PaprikaToAppleNotesConverter(source_dir, output_dir)
    converter.convert()
    
    return 0


if __name__ == '__main__':
    exit(main())