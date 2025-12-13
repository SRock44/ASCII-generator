"""Test 2: ExampleLoader functionality tests."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples_loader import ExampleLoader


def test_example_loader_initialization():
    """Test that ExampleLoader can be initialized."""
    loader = ExampleLoader()
    assert loader.examples_dir.exists() or loader.examples_dir.parent.exists(), \
        "Examples directory should exist or be creatable"
    assert loader._index is None, "Index should be None initially (lazy loading)"
    assert len(loader._cache) == 0, "Cache should be empty initially"
    print("✓ ExampleLoader initializes correctly")


def test_example_loader_lazy_loading():
    """Test that ExampleLoader loads index lazily."""
    loader = ExampleLoader()
    
    # Index should not be loaded initially
    assert loader._index is None, "Index should not be loaded initially"
    
    # Accessing index should load it
    index = loader._load_index()
    assert index is not None, "Index should be loaded after first access"
    assert isinstance(index, dict), "Index should be a dictionary"
    assert "keywords" in index or len(index) == 0, "Index should have expected structure"
    
    print("✓ Lazy loading works correctly")


def test_example_loader_get_examples():
    """Test that ExampleLoader can retrieve examples."""
    loader = ExampleLoader()
    
    # Try to get examples for a common subject
    examples = loader.get_examples("cat")
    
    # Should return a list (empty if no examples found, but should not crash)
    assert isinstance(examples, list), "get_examples should return a list"
    
    # If examples exist, they should have the right structure
    if examples:
        example = examples[0]
        assert "art" in example, "Example should have 'art' key"
        assert "lines" in example, "Example should have 'lines' key"
        assert "width" in example, "Example should have 'width' key"
        print(f"✓ Found {len(examples)} example(s) for 'cat'")
    else:
        print("✓ get_examples returns empty list when no examples found (graceful fallback)")
    
    print("✓ ExampleLoader.get_examples works correctly")


def test_example_loader_cache_eviction():
    """Test that ExampleLoader cache eviction works."""
    loader = ExampleLoader()
    
    # Fill cache to exactly MAX_CACHE_SIZE
    for i in range(loader.MAX_CACHE_SIZE):
        loader._cache[f"subject_{i}"] = {"examples": []}
        loader._access_times[f"subject_{i}"] = i
    
    # Add one more to trigger eviction
    loader._cache[f"subject_overflow"] = {"examples": []}
    loader._access_times[f"subject_overflow"] = 999
    
    # Now trigger eviction
    loader._evict_if_needed()
    
    # Cache should not exceed MAX_CACHE_SIZE
    # Note: eviction removes one item, so we should have MAX_CACHE_SIZE items
    assert len(loader._cache) <= loader.MAX_CACHE_SIZE, \
        f"Cache should not exceed {loader.MAX_CACHE_SIZE} items (got {len(loader._cache)})"
    
    print(f"✓ Cache eviction works correctly (cache size: {len(loader._cache)})")


if __name__ == "__main__":
    test_example_loader_initialization()
    test_example_loader_lazy_loading()
    test_example_loader_get_examples()
    test_example_loader_cache_eviction()
    print("\nTest 2 passed: ExampleLoader functionality")

