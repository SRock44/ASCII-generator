# Installation & Setup Guide

## Quick Start - Simple CLI Usage

There are **3 ways** to use ASCII-Generator with the easy `ascii` command:

---

## Option 1: Direct Script (Recommended for Development)

### Installation
```bash
# Navigate to project directory
cd ~/Projects/ASCII-Generator

# Make the script executable (already done)
chmod +x ascii

# Add to your PATH for system-wide access
export PATH="$PATH:$HOME/Projects/ASCII-Generator"
```

### Make it Permanent
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# ASCII Generator
export PATH="$PATH:$HOME/Projects/ASCII-Generator"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Usage
```bash
# Now you can use it from anywhere!
ascii art "a cat"
ascii chart "sales: Q1=100, Q2=150, Q3=200"
ascii diagram "user login flow" --live
```

---

## Option 2: Install as Python Package (Recommended for Production)

### Installation
```bash
# Navigate to project directory
cd ~/Projects/ASCII-Generator

# Install in development mode (changes reflect immediately)
pip install -e .

# OR install normally
pip install .
```

### Usage
```bash
# The 'ascii' command is now available globally!
ascii art "a dragon"
ascii chart "revenue data" --live --provider groq
ascii diagram "authentication flow" --orientation left-to-right
```

### Uninstall
```bash
pip uninstall ascii-generator
```

---

## Option 3: Shell Alias (Simplest)

### Setup
Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# ASCII Generator alias
alias ascii='cd ~/Projects/ASCII-Generator && python cli.py'
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Usage
```bash
ascii art "a cat"
ascii chart "sales data"
```

**Note:** This changes your directory when you run the command.

---

## Verification

Test your installation:

```bash
# Check if 'ascii' command is available
which ascii

# Test it
ascii art "hello world" --provider groq

# Check version
ascii --version
```

---

## All Available Commands

Once installed, you can use:

```bash
# ASCII Art
ascii art "a cat" [--live] [--explain] [--provider groq|gemini]

# Charts
ascii chart "sales: Q1=100, Q2=150" [--live] [--explain]

# Diagrams
ascii diagram "login flow" [--live] [--orientation top-to-bottom|left-to-right]

# Codebase Analysis
ascii codebase /path/to/project [--max-files 50]

# GitHub Repository Analysis
ascii github owner/repo [--max-files 50]

# Cache Management
ascii clear-cache

# Health Check
ascii check
```

---

## Common Flags

| Flag | Description |
|------|-------------|
| `--live` | Show live progressive drawing animation |
| `--provider groq` | Use Groq API (default: auto) |
| `--provider gemini` | Use Gemini API |
| `--no-cache` | Disable caching for this request |
| `--no-colors` | Disable color output (monochrome) |
| `--explain` | Get explanation (charts/art only) |
| `--orientation left-to-right` | Horizontal diagram flow |
| `--orientation top-to-bottom` | Vertical diagram flow (default) |

---

## Examples

```bash
# Simple art
ascii art "a cat"

# Live animation with Groq
ascii art "a dragon" --live --provider groq

# Chart with explanation
ascii chart "Q1=100, Q2=150, Q3=200" --live --explain

# Complex diagram
ascii diagram "oauth2 authentication flow" --orientation left-to-right

# Analyze codebase
ascii codebase . --max-files 100

# Debug mode
DEBUG=1 ascii art "test"
```

---

## Troubleshooting

### "ascii: command not found"

**If using Option 1 (Direct Script):**
```bash
# Check PATH
echo $PATH | grep ASCII-Generator

# If not there, add it
export PATH="$PATH:$HOME/Projects/ASCII-Generator"
```

**If using Option 2 (Python Package):**
```bash
# Reinstall
pip install -e .

# Check installation
pip show ascii-generator
```

**If using Option 3 (Alias):**
```bash
# Check alias
alias | grep ascii

# Reload shell config
source ~/.bashrc
```

### Permission Denied

```bash
# Make script executable
chmod +x ~/Projects/ASCII-Generator/ascii
```

### Module Not Found

```bash
# Activate virtual environment
cd ~/Projects/ASCII-Generator
source .venv/bin/activate

# Then use one of the installation methods above
```

---

## Recommended Setup

For the **best experience**, we recommend:

1. **Use Option 2** (Python package installation)
2. **Activate virtual environment** first
3. **Install in development mode**: `pip install -e .`

This gives you:
- ✅ Global `ascii` command
- ✅ Changes reflect immediately (dev mode)
- ✅ Clean uninstall (`pip uninstall ascii-generator`)
- ✅ Works from any directory

---

## Advanced: System-Wide Installation

To make `ascii` available for **all users** on the system:

```bash
# Install globally (requires sudo)
cd ~/Projects/ASCII-Generator
sudo pip install .

# Now all users can use 'ascii' command
```

**Warning:** This installs system-wide. Prefer user installation or virtual environments.

---

## Next Steps

After installation:

1. **Set up API keys** (see main README.md)
2. **Test the command**: `ascii art "hello"`
3. **Explore features**: `ascii --help`
4. **Read docs**: Check `IMPROVEMENTS.md` and `STRICT_MODE.md`

Enjoy your simplified CLI! 🎨✨
