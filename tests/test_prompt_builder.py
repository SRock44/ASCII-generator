"""Test 3: PromptBuilder functionality tests."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prompt_builder import PromptBuilder
from examples_loader import ExampleLoader


def test_prompt_builder_initialization():
    """Test that PromptBuilder can be initialized."""
    builder = PromptBuilder()
    assert builder.example_loader is not None, "ExampleLoader should be created"
    assert isinstance(builder.example_loader, ExampleLoader), \
        "ExampleLoader should be an ExampleLoader instance"
    print("✓ PromptBuilder initializes correctly")


def test_prompt_builder_builds_prompt():
    """Test that PromptBuilder can build prompts."""
    builder = PromptBuilder()
    
    # Build a prompt for ASCII art
    prompt = builder.build("cat", is_logo=False, max_examples=2)
    
    assert isinstance(prompt, str), "Prompt should be a string"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    # Should contain base prompt content
    assert "ASCII" in prompt or "ascii" in prompt.lower(), \
        "Prompt should contain ASCII-related content"
    
    print(f"✓ Built prompt ({len(prompt)} chars)")


def test_prompt_builder_logo_mode():
    """Test that PromptBuilder handles logo mode."""
    builder = PromptBuilder()
    
    # Build a prompt for logo
    logo_prompt = builder.build("test logo", is_logo=True, max_examples=2)
    
    assert isinstance(logo_prompt, str), "Logo prompt should be a string"
    assert len(logo_prompt) > 0, "Logo prompt should not be empty"
    
    print("✓ Logo mode works correctly")


def test_prompt_builder_graceful_fallback():
    """Test that PromptBuilder gracefully handles missing examples."""
    builder = PromptBuilder()
    
    # Try with a subject that likely doesn't exist
    prompt = builder.build("nonexistent_subject_xyz123", is_logo=False, max_examples=2)
    
    # Should still return a valid prompt (fallback to base prompt)
    assert isinstance(prompt, str), "Should return a prompt even without examples"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    print("✓ Graceful fallback when no examples found")


if __name__ == "__main__":
    test_prompt_builder_initialization()
    test_prompt_builder_builds_prompt()
    test_prompt_builder_logo_mode()
    test_prompt_builder_graceful_fallback()
    print("\nTest 3 passed: PromptBuilder functionality")


