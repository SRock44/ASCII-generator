# Test Suite

This directory contains tests for the ASCII-Generator project.

**All tests run without requiring external dependencies or environment setup.** They focus on syntax validation and basic functionality that can be verified in CI.

## Test Structure

### Test 1: Syntax Check (`test_syntax.py`)
- Verifies all Python files compile without syntax errors
- Checks all `.py` files in the project (excluding venv and test files)
- Ensures code quality at the basic level
- **No dependencies required** - uses standard library only

### Test 2: ExampleLoader (`test_example_loader.py`)
- Tests ExampleLoader initialization
- Verifies lazy loading behavior
- Tests example retrieval functionality
- Validates cache eviction mechanism
- **No external dependencies** - only uses standard library (json, pathlib)

### Test 3: PromptBuilder (`test_prompt_builder.py`)
- Tests PromptBuilder initialization
- Verifies prompt building functionality
- Tests logo mode handling
- Validates graceful fallback when no examples found
- **No external dependencies** - only uses ExampleLoader and standard library

### Test 4: Basic Functionality (`test_generator_init.py`)
- Tests logo detection logic (pure function testing)
- Verifies file structure exists
- Validates core module structure
- **No external dependencies** - tests logic and structure only

### Test 5: Integration (`test_integration.py`)
- Tests ExampleLoader + PromptBuilder integration
- Verifies PromptBuilder standalone usage
- Tests complete example loading chain
- Validates different prompt modes
- Tests graceful handling of missing examples
- **No external dependencies** - only uses ExampleLoader and PromptBuilder

## Running Tests

### Run all tests:
```bash
python3 tests/test_syntax.py
python3 tests/test_example_loader.py
python3 tests/test_prompt_builder.py
python3 tests/test_generator_init.py
python3 tests/test_integration.py
```

### Run all at once:
```bash
python3 tests/test_syntax.py && \
python3 tests/test_example_loader.py && \
python3 tests/test_prompt_builder.py && \
python3 tests/test_generator_init.py && \
python3 tests/test_integration.py
```

## CI/CD

Tests run automatically on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

The CI pipeline:
- Tests against Python 3.10, 3.11, and 3.12
- **No dependency installation required** - tests use only standard library
- Fast execution - no external API calls or environment setup needed

## Design Philosophy

These tests are designed to:
- ✅ Run in any environment (no venv/env required)
- ✅ Validate syntax and basic functionality
- ✅ Catch breaking changes early
- ✅ Run fast in CI (no external dependencies)
- ❌ Not test full integration with AI APIs (requires API keys)
- ❌ Not test components that need full environment setup

This ensures every commit is validated for code quality and basic functionality without requiring complex CI setup.

