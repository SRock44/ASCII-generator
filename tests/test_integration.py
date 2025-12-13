"""Test 5: Integration tests for ExampleLoader + PromptBuilder (no external deps)."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples_loader import ExampleLoader
from prompt_builder import PromptBuilder


def test_loader_builder_integration():
    """Test that ExampleLoader and PromptBuilder work together."""
    loader = ExampleLoader()
    builder = PromptBuilder(loader)
    
    # Build a prompt - should use loader
    prompt = builder.build("cat", is_logo=False, max_examples=2)
    
    assert isinstance(prompt, str), "Should return a prompt string"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    print("✓ ExampleLoader + PromptBuilder integration works")


def test_prompt_builder_standalone():
    """Test PromptBuilder can work standalone (creates its own loader)."""
    builder = PromptBuilder()
    
    # Should work without explicitly passing loader
    assert builder.example_loader is not None, "Should create ExampleLoader automatically"
    
    prompt = builder.build("elephant", is_logo=False, max_examples=2)
    assert isinstance(prompt, str), "Should return a prompt string"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    print("✓ PromptBuilder works standalone")


def test_example_loading_chain():
    """Test the complete chain: loader -> builder -> prompt."""
    loader = ExampleLoader()
    builder = PromptBuilder(loader)
    
    # Try to get examples and build prompt
    examples = loader.get_examples("cat")
    prompt = builder.build("cat", is_logo=False, max_examples=2)
    
    # Both should work without errors
    assert isinstance(examples, list), "Examples should be a list"
    assert isinstance(prompt, str), "Prompt should be a string"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    print("✓ Complete example loading chain works")


def test_prompt_builder_modes():
    """Test PromptBuilder in different modes."""
    builder = PromptBuilder()
    
    # Test ASCII art mode
    art_prompt = builder.build("cat", is_logo=False, max_examples=2)
    assert isinstance(art_prompt, str), "Art prompt should be a string"
    assert len(art_prompt) > 0, "Art prompt should not be empty"
    
    # Test logo mode
    logo_prompt = builder.build("test logo", is_logo=True, max_examples=2)
    assert isinstance(logo_prompt, str), "Logo prompt should be a string"
    assert len(logo_prompt) > 0, "Logo prompt should not be empty"
    
    # Prompts should be different
    assert art_prompt != logo_prompt, "Art and logo prompts should differ"
    
    print("✓ PromptBuilder handles different modes correctly")


def test_graceful_handling_missing_examples():
    """Test that system gracefully handles subjects with no examples."""
    loader = ExampleLoader()
    builder = PromptBuilder(loader)
    
    # Try with a subject that likely doesn't exist
    examples = loader.get_examples("nonexistent_subject_xyz123")
    prompt = builder.build("nonexistent_subject_xyz123", is_logo=False, max_examples=2)
    
    # Should return empty list for examples
    assert isinstance(examples, list), "Should return a list (even if empty)"
    
    # Should still return a valid prompt (fallback to base)
    assert isinstance(prompt, str), "Should return a prompt even without examples"
    assert len(prompt) > 0, "Prompt should not be empty"
    
    print("✓ Graceful handling of missing examples works")


if __name__ == "__main__":
    test_loader_builder_integration()
    test_prompt_builder_standalone()
    test_example_loading_chain()
    test_prompt_builder_modes()
    test_graceful_handling_missing_examples()
    print("\nTest 5 passed: Integration tests")
