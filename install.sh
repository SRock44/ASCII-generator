#!/bin/bash
# ASCII-Generator Easy Installation Script
# This script installs ASCII-Generator and sets up the global alias

set -e

echo "======================================================================"
echo "  ASCII-Generator Installation"
echo "======================================================================"
echo ""

# Get project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$PROJECT_DIR/.venv"

echo "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Check for virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please create it first:"
    echo "  python3 -m venv .venv"
    exit 1
fi

echo "Found virtual environment"
echo ""

# Step 2: Install package
echo "Installing ASCII-Generator..."
source "$VENV_DIR/bin/activate"
pip install -e . --quiet
echo "Package installed"
echo ""

# Step 3: Detect shell
SHELL_NAME=$(basename "$SHELL")
if [ "$SHELL_NAME" = "bash" ]; then
    RC_FILE="$HOME/.bashrc"
elif [ "$SHELL_NAME" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    echo "Unknown shell: $SHELL_NAME"
    echo "Please manually add this alias to your shell configuration:"
    echo "  alias ascii='source $PROJECT_DIR/.venv/bin/activate && ascii'"
    exit 0
fi

echo "Detected shell: $SHELL_NAME"
echo "Configuration file: $RC_FILE"
echo ""

# Step 4: Check if alias/function already exists
FUNCTION_LINE="ascii() { (source $PROJECT_DIR/.venv/bin/activate && command ascii \"\$@\") }"

if grep -q "ascii()" "$RC_FILE" 2>/dev/null || grep -q "alias ascii=" "$RC_FILE" 2>/dev/null; then
    echo "Found existing 'ascii' command in $RC_FILE"
    echo ""
    read -p "Do you want to UPDATE it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old alias or function
        sed -i.bak '/alias ascii=/d' "$RC_FILE"
        sed -i.bak '/^ascii() {/,/^}$/d' "$RC_FILE"
        echo "Removed old command"
    else
        echo "Skipping command setup."
        echo ""
        echo "======================================================================"
        echo "  Installation Complete!"
        echo "======================================================================"
        exit 0
    fi
fi

# Step 5: Add function (runs in subshell so venv doesn't affect parent shell)
echo "Adding function to $RC_FILE..."
echo "" >> "$RC_FILE"
echo "# ASCII-Generator - Global command (runs in subshell to avoid venv prompt)" >> "$RC_FILE"
echo "$FUNCTION_LINE" >> "$RC_FILE"
echo "Function added"
echo ""

# Step 6: Success message
echo "======================================================================"
echo "  Installation Complete!"
echo "======================================================================"
echo ""
echo "ASCII-Generator is now installed!"
echo ""
echo "Next Steps:"
echo ""
echo "1. Reload your shell configuration:"
echo "   source $RC_FILE"
echo ""
echo "2. Run the setup wizard (first time only):"
echo "   ascii check"
echo ""
echo "3. Generate your first ASCII art:"
echo "   ascii art \"a cat\" --live"
echo ""
echo "======================================================================"
echo "  You can now use 'ascii' from ANY directory! No venv activation needed."
echo "======================================================================"
echo ""
