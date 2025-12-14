"""Test 1: Syntax and compilation check for all Python files."""
import py_compile
import sys
from pathlib import Path


def test_all_python_files_compile():
    """Test that all Python files in the project compile without syntax errors."""
    project_root = Path(__file__).parent.parent
    python_files = []
    
    # Find all Python files
    for py_file in project_root.rglob("*.py"):
        # Skip venv and __pycache__
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        # Skip test files themselves
        if "test_" in py_file.name:
            continue
        python_files.append(py_file)
    
    errors = []
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{py_file}: {e}")
    
    if errors:
        print("\nSyntax errors found:")
        for error in errors:
            print(f"  {error}")
        assert False, f"Found {len(errors)} syntax error(s)"
    
    print(f"✓ All {len(python_files)} Python files compile successfully")


if __name__ == "__main__":
    test_all_python_files_compile()
    print("Test 1 passed: All files compile")


