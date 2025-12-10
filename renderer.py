"""Terminal rendering with Rich library."""
from typing import Optional
from rich.console import Console
from rich.text import Text
import config
import re


class Renderer:
    """Terminal renderer using Rich library."""
    
    def __init__(self):
        """Initialize renderer."""
        self.console = Console()
    
    def render_ascii(self, content: str, title: Optional[str] = None, use_colors: bool = True):
        """
        Render ASCII art/content with proper alignment and optional colors.
        
        Args:
            content: ASCII content to render
            title: Optional title for the content
            use_colors: Whether to apply color highlighting to ASCII art
        """
        # Clean up content
        content = content.strip()
        
        # Remove any markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Fix alignment issues - detect and fix inconsistent leading whitespace
        lines = content.split("\n")
        if lines:
            # Calculate leading spaces for each non-empty line
            leading_spaces = []
            for line in lines:
                if line.strip():
                    leading_spaces.append(len(line) - len(line.lstrip()))
            
            if leading_spaces:
                min_leading = min(leading_spaces)
                max_leading = max(leading_spaces)
                
                # If there's a significant misalignment (some lines at 0, others indented)
                # and the difference is large, we likely have an alignment issue
                has_zero_leading = 0 in leading_spaces
                has_indented = max_leading > 5
                
                if has_zero_leading and has_indented and max_leading - min_leading > 5:
                    # Fix alignment: ensure all lines have at least some consistent base indentation
                    # Find the most common leading space value (excluding 0)
                    non_zero_leading = [ls for ls in leading_spaces if ls > 0]
                    if non_zero_leading:
                        # Use the minimum non-zero leading as the base
                        base_indent = min(non_zero_leading)
                        normalized_lines = []
                        for line in lines:
                            if line.strip():
                                current_leading = len(line) - len(line.lstrip())
                                if current_leading == 0:
                                    # Add base indent to lines that have none
                                    normalized_lines.append(" " * base_indent + line.lstrip())
                                else:
                                    # Keep existing indentation
                                    normalized_lines.append(line)
                            else:
                                normalized_lines.append("")
                        content = "\n".join(normalized_lines)
        
        if title:
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
        
        # Apply colors if enabled
        if use_colors:
            colored_content = self._apply_ascii_colors(content)
            self.console.print(colored_content)
        else:
            # Use monospace font for ASCII art
            self.console.print(content, style="white")
        self.console.print()  # Extra newline
    
    def _apply_ascii_colors(self, content: str) -> Text:
        """
        Apply colors to ASCII art based on character patterns.
        
        Args:
            content: ASCII art content
            
        Returns:
            Rich Text object with colors applied
        """
        text = Text()
        lines = content.split("\n")
        
        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:  # Don't add newline after last line
                    text.append("\n")
                continue
            
            i = 0
            while i < len(line):
                char = line[i]
                
                # Color patterns based on character type
                if char in ['/', '\\', '|', '_', '-', '=']:
                    # Structural elements - cyan/blue
                    text.append(char, style="cyan")
                elif char in ['(', ')', '[', ']', '{', '}', '<', '>']:
                    # Brackets/parentheses - yellow
                    text.append(char, style="yellow")
                elif char in ['@', '#', '%']:
                    # Dense shading - bright white
                    text.append(char, style="bright_white")
                elif char == '*':
                    # Stars/sparkles - bright yellow
                    text.append(char, style="bright_yellow")
                elif char in ['.', ':', ',', ';']:
                    # Light details - green
                    text.append(char, style="green")
                elif char in ['^', 'v', 'V']:
                    # Arrows/triangles - red
                    text.append(char, style="red")
                elif char.lower() in ['o', '0']:
                    # Eyes/circles - bright yellow or bright cyan
                    text.append(char, style="bright_yellow")
                elif char in ['"', "'", '`']:
                    # Quotes/strings - magenta
                    text.append(char, style="magenta")
                elif char in ['~', '^']:
                    # Decorative - bright magenta
                    text.append(char, style="bright_magenta")
                elif char.isalnum():
                    # Letters/numbers - white
                    text.append(char, style="white")
                elif char == ' ':
                    # Spaces - keep as is (no color)
                    text.append(char)
                else:
                    # Default - white
                    text.append(char, style="white")
                
                i += 1
            
            if line_idx < len(lines) - 1:  # Don't add newline after last line
                text.append("\n")
        
        return text
    
    def render_error(self, message: str):
        """
        Render error message.
        
        Args:
            message: Error message (may contain ERROR_CODE and ERROR_MESSAGE format)
        """
        # Check if message contains error code format
        if "ERROR_CODE:" in message and "ERROR_MESSAGE:" in message:
            lines = message.split("\n")
            error_code = None
            error_message = None
            
            for line in lines:
                if line.startswith("ERROR_CODE:"):
                    error_code = line.replace("ERROR_CODE:", "").strip()
                elif line.startswith("ERROR_MESSAGE:"):
                    error_message = line.replace("ERROR_MESSAGE:", "").strip()
            
            if error_code and error_message:
                self.console.print(f"[bold red]Error Code:[/bold red] [yellow]{error_code}[/yellow]")
                self.console.print(f"[bold red]Error Message:[/bold red] {error_message}")
            else:
                self.console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            self.console.print(f"[bold red]Error:[/bold red] {message}")
    
    def render_info(self, message: str):
        """
        Render info message.
        
        Args:
            message: Info message
        """
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")
    
    def render_success(self, message: str):
        """
        Render success message.
        
        Args:
            message: Success message
        """
        self.console.print(f"[bold green]Success:[/bold green] {message}")
    
    def render_loading(self, message: str = "Generating..."):
        """
        Render loading message.
        
        Args:
            message: Loading message
        """
        self.console.print(f"[yellow]{message}[/yellow]", end="\r")
    
    def clear_line(self):
        """Clear the current line."""
        self.console.print(" " * 80, end="\r")

