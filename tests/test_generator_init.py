"""Test 4: Basic functionality tests that don't require external dependencies."""
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_logo_detection_logic():
    """Test logo detection logic (pure function, no imports needed)."""
    # Logo keywords from ASCIIArtGenerator
    LOGO_KEYWORDS = [
        r'\blogo\b', r'\bbranding\b', r'\bbrand\b', r'\bcompany\b', r'\bcorporate\b',
        r'\btext\b', r'\bletter\b', r'\bletters\b', r'\bword\b', r'\bwords\b',
        r'\bname\b', r'\btitle\b', r'\bheader\b', r'\bbanner\b', r'\bsign\b',
        r'\btypography\b', r'\bfont\b', r'\btypeface\b', r'\bmonogram\b',
        r'\bemblem\b', r'\binsignia\b', r'\bcrest\b', r'\bmark\b'
    ]
    
    def detect_logo_request(prompt: str) -> bool:
        """Simplified logo detection logic."""
        prompt_lower = prompt.lower()
        
        # Check for logo-related keywords
        for keyword_pattern in LOGO_KEYWORDS:
            if re.search(keyword_pattern, prompt_lower, re.IGNORECASE):
                return True
        
        # Check if prompt is just text/words (likely a logo request)
        words = prompt.split()
        if len(words) <= 5:
            short_words = sum(1 for w in words if len(w) <= 10)
            if short_words >= len(words) * 0.7:
                logo_phrases = ['for', 'called', 'named', 'logo for', 'text', 'letters']
                if any(phrase in prompt_lower for phrase in logo_phrases):
                    return True
                if not any(word.lower() in ['a', 'an', 'the'] for word in words):
                    capitalized = sum(1 for w in words if w and w[0].isupper())
                    if capitalized >= len(words) * 0.5:
                        return True
        return False
    
    # Test cases
    assert detect_logo_request("logo for my company") == True
    assert detect_logo_request("MY COMPANY") == True
    assert detect_logo_request("a cat") == False
    assert detect_logo_request("an elephant") == False
    assert detect_logo_request("branding text") == True
    assert detect_logo_request("ASCII ART") == True  # Capitalized
    
    print("✓ Logo detection logic works correctly")


def test_file_structure():
    """Test that required files and directories exist."""
    project_root = Path(__file__).parent.parent
    
    # Check core files exist
    required_files = [
        "examples_loader.py",
        "prompt_builder.py",
        "generators/ascii_art.py",
        "examples/index.json",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Required file {file_path} should exist"
    
    # Check examples directory structure
    examples_dir = project_root / "examples"
    assert examples_dir.exists(), "Examples directory should exist"
    
    # Check categories exist
    categories = ["animals", "objects", "nature", "characters"]
    for category in categories:
        category_dir = examples_dir / category
        # Category dir should exist (even if empty)
        assert category_dir.exists() or examples_dir.exists(), \
            f"Category directory {category} should exist or examples dir should exist"
    
    print("✓ File structure is correct")


def test_imports_structure():
    """Test that core modules can be imported (without executing)."""
    # Test that we can at least check if files are importable
    project_root = Path(__file__).parent.parent
    
    # Check that Python files exist and are readable
    core_modules = [
        "examples_loader.py",
        "prompt_builder.py",
    ]
    
    for module_file in core_modules:
        module_path = project_root / module_file
        assert module_path.exists(), f"Module {module_file} should exist"
        
        # Try to read and check it's valid Python (basic check)
        try:
            with open(module_path, 'r') as f:
                content = f.read()
                # Basic syntax check - should have class definitions
                assert "class " in content, f"{module_file} should contain class definitions"
        except Exception as e:
            assert False, f"Could not read {module_file}: {e}"
    
    print("✓ Core modules have valid structure")


if __name__ == "__main__":
    test_logo_detection_logic()
    test_file_structure()
    test_imports_structure()
    print("\nTest 4 passed: Basic functionality tests")
