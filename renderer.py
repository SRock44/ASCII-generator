"""Terminal rendering with Rich library."""
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.live import Live
import config
import re
import time
from colorizer import ASCIIColorizer


class Renderer:
    """Terminal renderer using Rich library."""
    
    def __init__(self, prompt: str = "", mode: str = "art"):
        """
        Initialize renderer.

        Args:
            prompt: User's original prompt for context-aware coloring
            mode: Generation mode ('art', 'chart', 'diagram')
        """
        self.console = Console()
        self.colorizer = ASCIIColorizer(prompt=prompt, mode=mode)
        self.prompt = prompt
        self.mode = mode
    
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
        
        # Apply intelligent colors if enabled
        # Colorizer will parse color hints from content and apply colors, then return clean art
        if use_colors:
            colored_content = self.colorizer.colorize(content)
            self.console.print(colored_content)
        else:
            # Strip color hints if present (even when colors are disabled)
            if "###COLORS###" in content:
                content = content.split("###COLORS###")[0].strip()
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
                
                # Box-drawing characters (Unicode box-drawing) - cyan
                if char in box_chars:
                    text.append(char, style="cyan")
                # Arrows - yellow
                elif char in ['→', '←', '↑', '↓']:
                    text.append(char, style="yellow")
                # ASCII box characters - cyan (for structural elements)
                elif char in ascii_box_chars:
                    # Check if it's likely a structural element vs text content
                    # Structural if: at line edges, or part of box pattern
                    is_structural = False
                    if i == 0 or i == len(line) - 1:
                        is_structural = True
                    elif char in ['/', '\\']:
                        # Check if surrounded by spaces or other structural chars
                        prev = line[i-1] if i > 0 else ' '
                        next = line[i+1] if i < len(line) - 1 else ' '
                        if prev in [' ', '_', '\\', '/', '|'] or next in [' ', '_', '\\', '/', '|']:
                            is_structural = True
                    elif char == '|':
                        # Vertical line - structural if not surrounded by alphanumeric
                        prev = line[i-1] if i > 0 else ' '
                        next = line[i+1] if i < len(line) - 1 else ' '
                        if not (prev.isalnum() and next.isalnum()):
                            is_structural = True
                    elif char in ['_', '-', '=']:
                        # Horizontal lines - structural if at edges or repeated
                        if i < 2 or i > len(line) - 3 or line.count(char) > 3:
                            is_structural = True
                    
                    if is_structural:
                        text.append(char, style="cyan")
                    else:
                        text.append(char, style="white")
                # All text content - white for consistency
                else:
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
    
    def render_explanation(self, explanation: str, title: Optional[str] = None):
        """
        Render explanation text.

        Args:
            explanation: Explanation text to render
            title: Optional title for the explanation
        """
        if title:
            self.console.print(f"\n[bold yellow]{title}[/bold yellow]\n")

        # Format explanation nicely
        self.console.print(f"[dim]{explanation}[/dim]")
        self.console.print()  # Extra newline

    def render_ascii_progressive(self, content_generator, title: Optional[str] = None, use_colors: bool = True, delay: float = 0.0):
        """
        Render ASCII art progressively as it's being generated (live drawing animation).
        OPTIMIZED: Minimal delay for maximum speed, only validated content is shown.

        Args:
            content_generator: Generator that yields VALIDATED chunks of text as they arrive
            title: Optional title for the content
            delay: Optional delay between rendering chunks (default: 0.0 for maximum speed)
            use_colors: Whether to apply color highlighting
        """
        if title:
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

        accumulated_content = ""

        # Use Rich Live for smooth updates (60fps for maximum smoothness)
        try:
            with Live(console=self.console, refresh_per_second=60, transient=False) as live:
                try:
                    retry_detected = False
                    for chunk in content_generator:
                        # Check for retry marker - this means previous output was broken
                        if "[RETRY]" in chunk:
                            retry_detected = True
                            # Clear accumulated content (broken output) and start fresh
                            accumulated_content = ""
                            # Remove the retry marker from chunk
                            chunk = chunk.replace("[RETRY]", "")
                            # Clear the display
                            live.update(Text())
                        
                        # Check for errors
                        if chunk and chunk.startswith("ERROR_CODE:"):
                            # Error occurred, render it and exit
                            error_lines = chunk.split("\n")
                            error_display = Text()
                            for line in error_lines:
                                error_display.append(line, style="red")
                                error_display.append("\n")
                            live.update(error_display)
                            break
                        
                        # Chunk is already validated by StreamingValidator
                        accumulated_content += chunk

                        # Split by lines and render progressively
                        # Colorizer will handle stripping color hints when it parses them
                        current_lines = accumulated_content.split("\n")

                        # Build display text
                        display_text = Text()

                        # Find where color hints section starts (if present)
                        color_section_start_idx = None
                        for idx, line in enumerate(current_lines):
                            if "###COLORS###" in line:
                                color_section_start_idx = idx
                                break
                        
                        for i, line in enumerate(current_lines):
                            # Skip lines that are part of the color hints section
                            if color_section_start_idx is not None and i >= color_section_start_idx:
                                continue  # Don't display color hints section
                            
                            # Strip color hints marker if it appears in the line itself
                            if "###COLORS###" in line:
                                line = line.split("###COLORS###")[0].strip()
                                if not line:
                                    continue  # Skip empty lines after stripping
                            
                            # For incomplete last line (might get more content), show it dimmed
                            if i == len(current_lines) - 1 and not accumulated_content.endswith("\n") and color_section_start_idx is None:
                                # Last incomplete line - show dimmed (only if not in color section)
                                if use_colors:
                                    colored_line = self.colorizer.colorize_line(line, i, is_incomplete=True, accumulated_content=accumulated_content)
                                    display_text.append(colored_line)
                                else:
                                    display_text.append(line, style="dim white")
                            else:
                                # Complete line
                                if use_colors:
                                    colored_line = self.colorizer.colorize_line(line, i, is_incomplete=False, accumulated_content=accumulated_content)
                                    display_text.append(colored_line)
                                else:
                                    display_text.append(line, style="white")

                            # Add newline except for last line
                            if i < len(current_lines) - 1:
                                display_text.append("\n")

                        # Update the live display immediately (no artificial delay)
                        live.update(display_text)

                        # Optional tiny delay for animation effect (default: none for max speed)
                        if delay > 0:
                            time.sleep(delay)
                    
                    # Final render of complete content after stream ends
                    # This ensures the final state is displayed even if stream ended abruptly
                    if accumulated_content.strip() and not accumulated_content.startswith("ERROR_CODE:"):
                        # Strip color hints for final display
                        final_content = accumulated_content
                        if "###COLORS###" in final_content:
                            final_content = final_content.split("###COLORS###")[0].strip()
                        
                        if final_content.strip():
                            final_lines = final_content.split("\n")
                            final_display = Text()
                            for i, line in enumerate(final_lines):
                                # Skip color hints section
                                if "###COLORS###" in line:
                                    break
                                if use_colors:
                                    colored_line = self.colorizer.colorize_line(line, i, is_incomplete=False, accumulated_content=accumulated_content)
                                    final_display.append(colored_line)
                                else:
                                    final_display.append(line, style="white")
                                if i < len(final_lines) - 1:
                                    final_display.append("\n")
                            live.update(final_display)
                except StopIteration:
                    # Generator exhausted - this is normal
                    pass
                except Exception as e:
                    # Log error but don't block
                    import sys
                    print(f"Error during progressive rendering: {e}", file=sys.stderr)
        finally:
            # Ensure Live context is properly closed
            pass

        # Final render with cleanup
        self.console.print()  # Extra newline

    def _apply_ascii_colors_to_line(self, line: str, is_incomplete: bool = False) -> Text:
        """
        Apply colors to a single line of ASCII art.

        Args:
            line: Single line of ASCII content
            is_incomplete: Whether this line is still being generated

        Returns:
            Rich Text object with colors applied
        """
        text = Text()

        # Box-drawing characters (Unicode box-drawing set)
        box_chars = '┌┐└┘├┤┬┴┼─│'
        # Regular ASCII box alternatives
        ascii_box_chars = ['/', '\\', '|', '_', '-', '=', '+']

        base_style = "dim white" if is_incomplete else "white"

        i = 0
        while i < len(line):
            char = line[i]

            # Box-drawing characters (Unicode box-drawing) - cyan
            if char in box_chars:
                text.append(char, style="dim cyan" if is_incomplete else "cyan")
            # Arrows - yellow
            elif char in ['→', '←', '↑', '↓']:
                text.append(char, style="dim yellow" if is_incomplete else "yellow")
            # ASCII box characters - cyan (for structural elements)
            elif char in ascii_box_chars:
                # Check if it's likely a structural element vs text content
                is_structural = False
                if i == 0 or i == len(line) - 1:
                    is_structural = True
                elif char in ['/', '\\']:
                    # Check if surrounded by spaces or other structural chars
                    prev = line[i-1] if i > 0 else ' '
                    next = line[i+1] if i < len(line) - 1 else ' '
                    if prev in [' ', '_', '\\', '/', '|'] or next in [' ', '_', '\\', '/', '|']:
                        is_structural = True
                elif char == '|':
                    # Vertical line - structural if not surrounded by alphanumeric
                    prev = line[i-1] if i > 0 else ' '
                    next = line[i+1] if i < len(line) - 1 else ' '
                    if not (prev.isalnum() and next.isalnum()):
                        is_structural = True
                elif char in ['_', '-', '=']:
                    # Horizontal lines - structural if at edges or repeated
                    if i < 2 or i > len(line) - 3 or line.count(char) > 3:
                        is_structural = True

                if is_structural:
                    text.append(char, style="dim cyan" if is_incomplete else "cyan")
                else:
                    text.append(char, style=base_style)
            # All text content
            else:
                text.append(char, style=base_style)

            i += 1

        return text

