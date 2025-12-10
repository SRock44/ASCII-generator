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
            line_info = []
            for i, line in enumerate(lines):
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    leading_spaces.append(leading)
                    line_info.append((i, leading, line))
            
            if leading_spaces and len(set(leading_spaces)) > 1:  # Multiple different indentations
                from collections import Counter
                leading_counts = Counter(leading_spaces)
                min_leading = min(leading_spaces)
                max_leading = max(leading_spaces)
                
                # Filter out lines with 0 or very few spaces (likely misaligned parts)
                # Focus on lines with substantial indentation (likely the main body)
                substantial_indents = [ls for ls in leading_spaces if ls >= 3]
                
                if substantial_indents:
                    # Use the most common substantial indentation as the base
                    substantial_counts = Counter(substantial_indents)
                    if substantial_counts:
                        base_indent = substantial_counts.most_common(1)[0][0]
                        
                        # Align all lines to the base indent for consistent alignment
                        # Only skip if variation is very small (1-2 spaces difference)
                        if max_leading - min_leading > 1:
                            normalized_lines = []
                            for i, line in enumerate(lines):
                                if line.strip():
                                    current_leading = len(line) - len(line.lstrip())
                                    
                                    # Align all lines to base_indent for consistency
                                    # Only preserve if it's exactly at base (within 1 space)
                                    if abs(current_leading - base_indent) <= 1:
                                        # Already aligned or very close, keep as is
                                        normalized_lines.append(line)
                                    else:
                                        # Align to base
                                        offset = base_indent - current_leading
                                        normalized_lines.append(" " * max(0, offset) + line.lstrip())
                                else:
                                    normalized_lines.append("")
                            content = "\n".join(normalized_lines)
                else:
                    # No substantial indents found, use median
                    sorted_leading = sorted(leading_spaces)
                    median_idx = len(sorted_leading) // 2
                    median_leading = sorted_leading[median_idx]
                    
                    normalized_lines = []
                    for line in lines:
                        if line.strip():
                            current_leading = len(line) - len(line.lstrip())
                            offset = median_leading - current_leading
                            if abs(offset) > 0:
                                normalized_lines.append(" " * max(0, offset) + line.lstrip())
                            else:
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
        For diagrams: box outlines are colored, text inside boxes is white.
        
        Args:
            content: ASCII art content
            
        Returns:
            Rich Text object with colors applied
        """
        text = Text()
        lines = content.split("\n")
        
        # Box-drawing characters (Unicode box-drawing set)
        box_chars = '┌┐└┘├┤┬┴┼─│'
        # Regular ASCII box alternatives
        ascii_box_chars = ['/', '\\', '|', '_', '-', '=', '+']
        
        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:  # Don't add newline after last line
                    text.append("\n")
                continue
            
            i = 0
            while i < len(line):
                char = line[i]
                
                # Box-drawing characters (diagram boxes) - cyan
                if char in box_chars:
                    text.append(char, style="cyan")
                # ASCII box characters - cyan
                elif char in ascii_box_chars:
                    text.append(char, style="cyan")
                # Arrows - yellow for diagrams, red for art
                elif char in ['→', '←', '↑', '↓']:
                    text.append(char, style="yellow")
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
                elif char in ['~']:
                    # Decorative - bright magenta
                    text.append(char, style="bright_magenta")
                elif char.isalnum() or char in [' ', '.', ',', ':', ';', '!', '?', '(', ')', '-']:
                    # Text content (letters, numbers, punctuation, spaces) - always white
                    # This ensures text inside boxes stays white
                    text.append(char, style="white")
                else:
                    # Default - white for any other character (likely text)
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

