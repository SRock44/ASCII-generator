#!/bin/bash
# ASCII-Generator Uninstallation Script
# This script removes ASCII-Generator and cleans up the global command

set -e

echo "======================================================================"
echo "  ASCII-Generator Uninstallation"
echo "======================================================================"
echo ""

# Get project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Detect shell
SHELL_NAME=$(basename "$SHELL")
if [ "$SHELL_NAME" = "bash" ]; then
    RC_FILE="$HOME/.bashrc"
elif [ "$SHELL_NAME" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    echo "Unknown shell: $SHELL_NAME"
    echo "Please manually remove the 'ascii' command from your shell configuration:"
    echo "  $RC_FILE"
    RC_FILE=""
fi

# Step 2: Remove function/alias from shell config
if [ -n "$RC_FILE" ] && [ -f "$RC_FILE" ]; then
    echo "Checking for ASCII-Generator command in $RC_FILE..."
    
    # Check if it exists (check for function, alias, or comment)
    if grep -q "ASCII-Generator" "$RC_FILE" 2>/dev/null || \
       grep -q "^ascii()" "$RC_FILE" 2>/dev/null || \
       grep -q "alias ascii=.*\.venv" "$RC_FILE" 2>/dev/null; then
        echo "Found ASCII-Generator command in $RC_FILE"
        echo ""
        read -p "Do you want to REMOVE it? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Create backup with timestamp
            BACKUP_FILE="$RC_FILE.bak.$(date +%Y%m%d_%H%M%S)"
            cp "$RC_FILE" "$BACKUP_FILE"
            
            # Remove the comment line (handle both comment formats)
            sed -i '/# ASCII-Generator - Global command/d' "$RC_FILE"
            
            # Remove single-line function definition (most common case)
            # The function is: ascii() { (source .../.venv/bin/activate && command ascii "$@") }
            # Match any line that starts with ascii() and contains .venv/bin/activate
            sed -i '/^ascii() {.*\.venv.*bin.*activate.*}$/d' "$RC_FILE"
            # Also match if it contains "command ascii"
            sed -i '/^ascii() {.*command ascii.*}$/d' "$RC_FILE"
            
            # Remove multi-line function definition (if it exists)
            # Pattern: ascii() { ... } on multiple lines
            # Match from function start to closing brace on new line
            sed -i '/^ascii() {/,/^}$/d' "$RC_FILE"
            
            # Use a more robust approach: remove any function that contains .venv/bin/activate
            # This handles both single-line and multi-line cases
            if command -v perl >/dev/null 2>&1; then
                # Remove function spanning multiple lines (perl can handle this better)
                perl -i -0pe 's/^ascii\(\) \{[^}]*\.venv[^}]*\}//gm' "$RC_FILE"
                perl -i -0pe 's/^ascii\(\) \{.*command ascii[^}]*\}//gm' "$RC_FILE"
            fi
            
            # Remove alias (old version) - handle various formats
            sed -i '/alias ascii=.*ASCII-Generator/d' "$RC_FILE"
            sed -i '/alias ascii=.*\.venv.*activate/d' "$RC_FILE"
            sed -i "/alias ascii='source.*\.venv.*activate/d" "$RC_FILE"
            sed -i '/alias ascii="source.*\.venv.*activate/d' "$RC_FILE"
            
            # Final cleanup: remove any remaining lines that start with ascii() 
            # (catch any we might have missed - be more aggressive)
            # Match any line starting with ascii() that contains venv or activate
            sed -i '/^ascii() {.*venv/d' "$RC_FILE"
            sed -i '/^ascii() {.*activate/d' "$RC_FILE"
            sed -i '/^ascii() {.*command ascii/d' "$RC_FILE"
            
            # Clean up multiple consecutive empty lines
            sed -i '/^$/N;/^\n$/d' "$RC_FILE"
            
            # Verify removal
            if grep -q "^ascii()" "$RC_FILE" 2>/dev/null || \
               grep -q "alias ascii=.*\.venv" "$RC_FILE" 2>/dev/null; then
                echo "⚠️  Warning: Some ASCII-Generator entries may still exist in $RC_FILE"
                echo "   Please check manually and remove any remaining 'ascii' function or alias"
            else
                echo "✓ Successfully removed ASCII-Generator command from $RC_FILE"
            fi
            
            echo "Backup saved to: $BACKUP_FILE"
            echo ""
            echo "⚠️  IMPORTANT: You MUST reload your shell for changes to take effect!"
            echo "   Run one of these commands:"
            echo "     source $RC_FILE"
            echo "     # OR simply start a new terminal"
            echo ""
            echo "   The 'ascii' command will still work in your CURRENT terminal"
            echo "   until you reload the shell configuration."
        else
            echo "Skipping command removal."
        fi
    else
        echo "No ASCII-Generator command found in $RC_FILE"
    fi
    echo ""
fi

# Step 3: Ask about virtual environment
echo "Virtual environment location: $PROJECT_DIR/.venv"
echo ""
read -p "Do you want to REMOVE the virtual environment? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$PROJECT_DIR/.venv" ]; then
        rm -rf "$PROJECT_DIR/.venv"
        echo "Removed virtual environment"
    else
        echo "Virtual environment not found (already removed?)"
    fi
else
    echo "Keeping virtual environment"
fi
echo ""

# Step 4: Ask about cache
CACHE_DIR="$PROJECT_DIR/.cache"
if [ -d "$CACHE_DIR" ]; then
    echo "Cache directory found: $CACHE_DIR"
    read -p "Do you want to REMOVE the cache? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CACHE_DIR"
        echo "Removed cache directory"
    else
        echo "Keeping cache directory"
    fi
    echo ""
fi

# Step 5: Ask about .env file
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Configuration file found: $ENV_FILE"
    read -p "Do you want to REMOVE the .env file (API keys)? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$ENV_FILE"
        echo "Removed .env file"
    else
        echo "Keeping .env file"
    fi
    echo ""
fi

# Step 6: Success message
echo "======================================================================"
echo "  Uninstallation Complete!"
echo "======================================================================"
echo ""
echo "ASCII-Generator has been uninstalled."
echo ""
if [ -n "$RC_FILE" ]; then
    echo "Next Steps:"
    echo ""
    echo "1. Reload your shell configuration:"
    echo "   source $RC_FILE"
    echo ""
    echo "2. The 'ascii' command will no longer be available."
    echo ""
fi
echo "======================================================================"
echo ""
