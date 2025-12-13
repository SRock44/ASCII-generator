#!/usr/bin/env python3
"""
Scrape ASCII art examples from ascii-art.de and save to JSON files.
Run once to build the example library.

Usage: 
    python scripts/scrape_examples.py              # Resume mode (skip existing)
    python scripts/scrape_examples.py --full       # Full scrape (overwrite)
    python scripts/scrape_examples.py --delay 1.0  # Custom delay between requests
"""

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Optional

# Base URL for ascii-art.de
BASE_URL = "https://www.ascii-art.de/ascii"

# Subjects to scrape, organized by category
SUBJECTS = {
    "animals": [
        ("cat", "c/cat.txt"),
        ("elephant", "def/elephant.txt"),
        ("horse", "ghi/horse.txt"),
        ("bird", "ab/bird.txt"),
        ("fish", "def/fish.txt"),
        ("snake", "s/snake.txt"),
        ("rabbit", "pqr/rabbit.txt"),
        ("lion", "jkl/lion.txt"),
        ("tiger", "t/tiger.txt"),
        ("bear", "ab/bear.txt"),
        ("wolf", "uvw/wolf.txt"),
        ("fox", "def/fox.txt"),
        ("eagle", "def/eagle.txt"),
        ("dolphin", "def/dolphin.txt"),
        ("whale", "uvw/whale.txt"),
        ("frog", "def/frog.txt"),
        ("turtle", "t/turtle.txt"),
        ("butterfly", "ab/butterfly.txt"),
        ("spider", "s/spider.txt"),
        ("bee", "ab/bee.txt"),
        ("monkey", "mno/monkey.txt"),
        ("pig", "pqr/pig.txt"),
        ("cow", "c/cow.txt"),
        ("chicken", "c/chicken.txt"),
        ("mouse", "mno/mouse.txt"),
    ],
    "objects": [
        ("car", "c/car.txt"),
        ("house", "ghi/house.txt"),
        ("computer", "c/computer.txt"),
        ("phone", "pqr/phone.txt"),
        ("guitar", "ghi/guitar.txt"),
        ("piano", "pqr/piano.txt"),
        ("boat", "ab/boat.txt"),
        ("plane", "pqr/plane.txt"),
        ("train", "t/train.txt"),
        ("bicycle", "ab/bicycle.txt"),
        ("clock", "c/clock.txt"),
        ("camera", "c/camera.txt"),
        ("cup", "c/cup.txt"),
        ("bottle", "ab/bottle.txt"),
        ("chair", "c/chair.txt"),
        ("table", "t/table.txt"),
        ("lamp", "jkl/lamp.txt"),
        ("key", "jkl/key.txt"),
    ],
    "nature": [
        ("tree", "t/tree.txt"),
        ("sun", "s/sun.txt"),
        ("moon", "mno/moon.txt"),
        ("star", "s/star.txt"),
        ("mountain", "mno/mountain.txt"),
        ("rain", "pqr/rain.txt"),
        ("fire", "def/fire.txt"),
        ("water", "uvw/water.txt"),
        ("rose", "pqr/rose.txt"),
        ("mushroom", "mno/mushroom.txt"),
    ],
    "characters": [
        ("dragon", "def/dragon.txt"),
        ("robot", "pqr/robot.txt"),
        ("wizard", "uvw/wizard.txt"),
        ("ghost", "ghi/ghost.txt"),
        ("skull", "s/skull.txt"),
        ("angel", "ab/angel.txt"),
        ("devil", "def/devil.txt"),
        ("santa", "s/santa.txt"),
        ("witch", "uvw/witch.txt"),
        ("pirate", "pqr/pirate.txt"),
        ("alien", "ab/alien.txt"),
        ("zombie", "xyz/zombie.txt"),
    ],
}

# Keywords for better matching
KEYWORD_EXPANSIONS = {
    "cat": ["cat", "kitten", "kitty", "feline"],
    "elephant": ["elephant", "elephants", "trunk", "tusks"],
    "horse": ["horse", "pony", "stallion", "mare", "equine"],
    "snake": ["snake", "python", "serpent", "cobra", "viper"],
    "rabbit": ["rabbit", "bunny", "hare"],
    "bird": ["bird", "sparrow", "finch"],
    "fish": ["fish", "goldfish", "tropical"],
    "lion": ["lion", "lions", "leo", "simba"],
    "tiger": ["tiger", "tigers", "bengal"],
    "bear": ["bear", "grizzly", "teddy"],
    "wolf": ["wolf", "wolves", "howl"],
    "fox": ["fox", "foxes", "vixen"],
    "eagle": ["eagle", "eagles", "hawk", "falcon"],
    "dolphin": ["dolphin", "dolphins", "porpoise"],
    "whale": ["whale", "whales", "orca"],
    "frog": ["frog", "frogs", "toad"],
    "turtle": ["turtle", "tortoise", "terrapin"],
    "butterfly": ["butterfly", "butterflies", "moth"],
    "spider": ["spider", "spiders", "tarantula", "web"],
    "bee": ["bee", "bees", "bumblebee", "honeybee"],
    "monkey": ["monkey", "ape", "chimp", "gorilla"],
    "pig": ["pig", "piggy", "hog", "boar"],
    "cow": ["cow", "cattle", "bull", "bovine"],
    "chicken": ["chicken", "hen", "rooster", "chick"],
    "mouse": ["mouse", "mice", "rat"],
    "car": ["car", "automobile", "vehicle", "auto"],
    "house": ["house", "home", "building", "cottage"],
    "computer": ["computer", "pc", "laptop", "desktop"],
    "phone": ["phone", "telephone", "mobile", "cellphone"],
    "guitar": ["guitar", "acoustic", "electric guitar"],
    "piano": ["piano", "keyboard", "grand piano"],
    "boat": ["boat", "ship", "sailboat", "yacht"],
    "plane": ["plane", "airplane", "aircraft", "jet"],
    "train": ["train", "locomotive", "railway"],
    "bicycle": ["bicycle", "bike", "cycle"],
    "tree": ["tree", "trees", "oak", "pine"],
    "sun": ["sun", "sunny", "sunshine", "solar"],
    "moon": ["moon", "lunar", "crescent"],
    "star": ["star", "stars", "starry"],
    "mountain": ["mountain", "mountains", "peak", "hill"],
    "dragon": ["dragon", "dragons", "drake", "wyvern"],
    "robot": ["robot", "robots", "android", "cyborg", "mech"],
    "wizard": ["wizard", "mage", "sorcerer", "magician"],
    "ghost": ["ghost", "phantom", "spirit", "spooky"],
    "skull": ["skull", "skeleton", "bones"],
    "angel": ["angel", "angels", "cherub", "seraph"],
    "devil": ["devil", "demon", "satan", "lucifer"],
    "santa": ["santa", "christmas", "claus", "xmas"],
    "witch": ["witch", "witches", "hag", "sorceress"],
    "pirate": ["pirate", "pirates", "buccaneer"],
    "alien": ["alien", "aliens", "ufo", "extraterrestrial", "et"],
    "zombie": ["zombie", "zombies", "undead"],
}


def fetch_url(url: str, retries: int = 3, delay: float = 1.0) -> Optional[str]:
    """Fetch URL content with error handling and retry logic."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (ASCII Art Scraper)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))  # Exponential backoff
                continue
            print(f"  Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
            return None
    return None


def extract_art_pieces(content: str, min_lines: int = 4, max_lines: int = 20) -> list:
    """
    Extract individual ASCII art pieces from a text file.
    Returns list of art strings that meet size criteria.
    """
    pieces = []

    # Split by common separators (blank lines, author credits, etc.)
    # Look for chunks separated by multiple newlines or artist signatures
    chunks = re.split(r'\n\s*\n\s*\n|\n-{5,}\n|\n_{5,}\n', content)

    for chunk in chunks:
        lines = chunk.strip().split('\n')

        # Filter out header/footer lines (often contain URLs, credits)
        art_lines = []
        for line in lines:
            # Skip lines that look like metadata
            if any(skip in line.lower() for skip in ['http', 'www.', '@', 'ascii-art.de', '(c)', 'copyright']):
                continue
            # Skip lines that are just dashes or equals (separators)
            if re.match(r'^[-=_~]{10,}$', line.strip()):
                continue
            art_lines.append(line)

        # Remove leading/trailing empty lines
        while art_lines and not art_lines[0].strip():
            art_lines.pop(0)
        while art_lines and not art_lines[-1].strip():
            art_lines.pop()

        if not art_lines:
            continue

        # Check size criteria
        line_count = len(art_lines)
        max_width = max(len(line) for line in art_lines) if art_lines else 0

        if min_lines <= line_count <= max_lines and max_width <= 70:
            # Calculate quality score (prefer balanced, not too sparse/dense)
            total_chars = sum(len(line) for line in art_lines)
            non_space = sum(len(line.replace(' ', '')) for line in art_lines)
            density = non_space / total_chars if total_chars > 0 else 0

            # Good density is 30-70%
            if 0.25 <= density <= 0.80:
                art = '\n'.join(art_lines)
                pieces.append({
                    'art': art,
                    'lines': line_count,
                    'width': max_width,
                    'density': round(density, 2)
                })

    # Sort by quality (prefer medium density, good line count)
    def quality_score(p):
        # Prefer 6-12 lines
        line_score = 1.0 - abs(p['lines'] - 9) / 10
        # Prefer 40-60% density
        density_score = 1.0 - abs(p['density'] - 0.5) * 2
        return line_score + density_score

    pieces.sort(key=quality_score, reverse=True)

    return pieces[:5]  # Return top 5 pieces


def scrape_subject(subject: str, url_path: str, category: str) -> Optional[dict]:
    """Scrape examples for a single subject."""
    url = f"{BASE_URL}/{url_path}"
    print(f"  Fetching {subject} from {url}...")

    content = fetch_url(url)
    if not content:
        return None

    pieces = extract_art_pieces(content)
    if not pieces:
        print(f"    No suitable art found for {subject}")
        return None

    print(f"    Found {len(pieces)} quality pieces")

    return {
        "subject": subject,
        "keywords": KEYWORD_EXPANSIONS.get(subject, [subject]),
        "category": category,
        "examples": pieces
    }


def build_index(examples_dir: Path) -> dict:
    """Build keyword index from all example files."""
    index = {
        "keywords": {},  # keyword -> subject
        "subjects": {},  # subject -> file path
        "categories": {}  # category -> [subjects]
    }

    for category_dir in examples_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue

        category = category_dir.name
        index["categories"][category] = []

        for json_file in category_dir.glob("*.json"):
            subject = json_file.stem
            rel_path = f"{category}/{json_file.name}"

            index["subjects"][subject] = rel_path
            index["categories"][category].append(subject)

            # Load keywords from file
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    for keyword in data.get("keywords", [subject]):
                        index["keywords"][keyword.lower()] = subject
            except Exception:
                index["keywords"][subject.lower()] = subject

    return index


def find_subject_info(subject_name: str) -> Optional[tuple]:
    """
    Find subject information by name across all categories.
    
    Args:
        subject_name: Subject name to find
        
    Returns:
        Tuple of (category, subject, url_path) or None if not found
    """
    subject_lower = subject_name.lower().strip()
    for category, subjects in SUBJECTS.items():
        for subject, url_path in subjects:
            if subject.lower() == subject_lower:
                return (category, subject, url_path)
    return None


def main(skip_existing: bool = True, delay: float = 0.5, target_subjects: Optional[list] = None):
    """
    Main scraping function.
    
    Args:
        skip_existing: If True, skip subjects that already have JSON files
        delay: Delay between requests in seconds (default: 0.5)
        target_subjects: Optional list of specific subjects to scrape (None = all)
    """
    # Examples directory is in ASCII-Generator project
    # This script can be run from ASCII-Scraper directory
    generator_dir = Path.home() / "Projects" / "ASCII-Generator"
    examples_dir = generator_dir / "examples"
    examples_dir.mkdir(exist_ok=True)

    print("ASCII Art Example Scraper")
    print("=" * 50)
    
    if target_subjects:
        print(f"Mode: Targeted scrape ({len(target_subjects)} subjects)")
    elif skip_existing:
        print("Mode: Resume (skipping existing files)")
    else:
        print("Mode: Full scrape (overwriting existing files)")
    print(f"Delay between requests: {delay}s")
    print()

    # Build list of subjects to scrape
    subjects_to_scrape = []
    
    if target_subjects:
        # Target specific subjects
        for subject_name in target_subjects:
            info = find_subject_info(subject_name)
            if info:
                category, subject, url_path = info
                subjects_to_scrape.append((category, subject, url_path))
            else:
                print(f"⚠️  Warning: Subject '{subject_name}' not found, skipping")
    else:
        # All subjects
        for category, subjects in SUBJECTS.items():
            for subject, url_path in subjects:
                subjects_to_scrape.append((category, subject, url_path))

    total = len(subjects_to_scrape)
    scraped = 0
    skipped = 0
    failed = []

    # Group by category for better output
    by_category = {}
    for category, subject, url_path in subjects_to_scrape:
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((subject, url_path))

    for category, subjects in by_category.items():
        print(f"\nCategory: {category}")
        print("-" * 30)

        category_dir = examples_dir / category
        category_dir.mkdir(exist_ok=True)

        for subject, url_path in subjects:
            output_file = category_dir / f"{subject}.json"
            
            # Skip if file exists and skip_existing is True
            if skip_existing and output_file.exists():
                try:
                    # Verify file is valid JSON with examples
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                        if data.get("examples"):
                            skipped += 1
                            print(f"    Skipping {subject} (already exists)")
                            continue
                except Exception:
                    # File exists but is invalid, re-scrape it
                    pass

            data = scrape_subject(subject, url_path, category)

            if data and data["examples"]:
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                scraped += 1
                print(f"    ✓ Saved {subject}.json ({len(data['examples'])} examples)")
            else:
                failed.append(subject)
                print(f"    ✗ Failed {subject}")

            # Be nice to the server
            time.sleep(delay)

    # Build index
    print("\nBuilding index...")
    index = build_index(examples_dir)
    with open(examples_dir / "index.json", 'w') as f:
        json.dump(index, f, indent=2)

    print("\n" + "=" * 50)
    print(f"Scraping complete!")
    print(f"  Total subjects: {total}")
    print(f"  Scraped: {scraped}")
    if skip_existing:
        print(f"  Skipped (existing): {skipped}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print(f"\n  Failed subjects: {', '.join(failed)}")
    print(f"\nIndex saved to {examples_dir}/index.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape ASCII art examples from ascii-art.de",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/scrape_examples.py                                    # Resume (skip existing)
  python scripts/scrape_examples.py --full                             # Full scrape (overwrite all)
  python scripts/scrape_examples.py --subjects dog,cat,elephant        # Scrape specific subjects
  python scripts/scrape_examples.py --subjects dog --delay 1.0          # Single subject, slower
        """
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full scrape mode: overwrite existing files (default: resume mode)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--subjects',
        type=str,
        help='Comma-separated list of specific subjects to scrape (e.g., "dog,cat,elephant")'
    )
    
    args = parser.parse_args()
    
    # Parse subjects if provided
    target_subjects = None
    if args.subjects:
        target_subjects = [s.strip() for s in args.subjects.split(',') if s.strip()]
    
    main(skip_existing=not args.full, delay=args.delay, target_subjects=target_subjects)
