"""Setup configuration for ASCII-Generator."""
from setuptools import setup
import os

# Read requirements
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Get the directory containing setup.py
here = os.path.abspath(os.path.dirname(__file__))

setup(
    name="ascii-generator",
    version="1.0.0",
    description="Generate ASCII art, charts, and diagrams using AI with strict validation",
    author="ASCII-Generator",
    python_requires=">=3.8",
    # Include all Python files in the project root
    py_modules=[
        'cli',
        'config',
        'rate_limiter',
        'renderer',
        'validators',
        'colorizer',
        'examples_loader',
        'prompt_builder',
        'session_context',
    ],
    # Include packages (subfolders with __init__.py)
    packages=['ai', 'generators', 'parsers'],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ascii=cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
