"""AI-powered intelligent ASCII art colorization."""
from typing import Optional, Dict
from rich.text import Text


class ASCIIColorizer:
    """
    AI-powered colorizer that uses color hints from the AI model.
    Falls back to simple hardcoded rules if no hints provided.
    """

    def __init__(self, prompt: str = "", mode: str = "art"):
        """
        Initialize colorizer.

        Args:
            prompt: User's original prompt
            mode: Generation mode ('art', 'chart', 'diagram')
        """
        self.mode = mode
        self.color_hints = {}  # Will be populated by parse_colors()

    def parse_color_hints(self, content: str) -> str:
        """
        Extract color hints from AI output and return clean ASCII art.

        Args:
            content: Full AI output (art + color hints)

        Returns:
            Clean ASCII art without color hints
        """
        if "###COLORS###" not in content:
            # No color hints, return as-is
            return content

        # Split content
        parts = content.split("###COLORS###")
        ascii_art = parts[0].strip()

        # Parse color hints if present
        if len(parts) > 1:
            color_lines = parts[1].strip().split("\n")
            for line in color_lines:
                if ":" in line:
                    feature, color = line.split(":", 1)
                    self.color_hints[feature.strip()] = color.strip()

        return ascii_art

    def colorize(self, content: str) -> Text:
        """
        Apply AI-suggested colors to ASCII art.

        Args:
            content: ASCII art content (may include color hints)

        Returns:
            Rich Text object with colors
        """
        # Parse and extract color hints
        clean_content = self.parse_color_hints(content)

        # Mode-specific coloring
        if self.mode == "diagram":
            return self._colorize_diagram(clean_content)
        elif self.mode == "chart":
            return self._colorize_chart(clean_content)
        else:
            return self._colorize_art(clean_content)

    def _colorize_art(self, content: str) -> Text:
        """
        Colorize ASCII art using AI-suggested colors with smart fallbacks.

        Uses color hints from AI when available, otherwise uses character-based rules.

        Args:
            content: ASCII art content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")

        # Get colors from AI hints or use defaults
        outline_color = self.color_hints.get('outline', 'bright_cyan')
        eyes_color = self.color_hints.get('eyes', 'bright_yellow')
        nose_color = self.color_hints.get('nose', 'bright_green')
        mouth_color = self.color_hints.get('mouth', 'bright_green')
        body_color = self.color_hints.get('body', 'white')
        hat_color = self.color_hints.get('hat', 'brown')
        ears_color = self.color_hints.get('ears', outline_color)

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            # Detect region (top = hat/ears, middle = body, etc.)
            total_lines = len([l for l in lines if l.strip()])
            is_top = line_idx < total_lines * 0.25

            for char in line:
                # Structural outlines - use AI color or default
                if char in '/\\|_-=+':
                    color = hat_color if is_top and 'hat' in self.color_hints else outline_color
                    text.append(char, style=color)

                # Eyes - use AI color
                elif char in 'oO@':
                    text.append(char, style=eyes_color)

                # Nose/mouth features - use AI color
                elif char in '<>v^':
                    # Check if it's nose or mouth based on position
                    text.append(char, style=nose_color)

                # Solid blocks - use body color
                elif char in '#█▓▒░':
                    text.append(char, style=body_color)

                # Dots and stars - bright magenta
                elif char in '.*':
                    text.append(char, style="bright_magenta")

                # Parentheses and brackets - cyan
                elif char in '(){}[]':
                    text.append(char, style="cyan")

                # Everything else (letters, numbers, spaces) - use body color
                else:
                    text.append(char, style=body_color)

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def _colorize_diagram(self, content: str) -> Text:
        """
        Colorize diagrams with clear, professional colors.

        Args:
            content: Diagram content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            for char in line:
                # Box corners - bright blue
                if char in '┌┐└┘├┤┬┴┼':
                    text.append(char, style="bright_blue")

                # Box lines - cyan
                elif char in '─│':
                    text.append(char, style="cyan")

                # Arrows - bright yellow
                elif char in '→←↑↓':
                    text.append(char, style="bright_yellow")

                # Letters and numbers - bright white
                elif char.isalnum():
                    text.append(char, style="bright_white")

                # Everything else - white
                else:
                    text.append(char, style="white")

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def _colorize_chart(self, content: str) -> Text:
        """
        Colorize charts with data visualization colors.

        Args:
            content: Chart content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            for char in line:
                # Box drawing - cyan
                if char in '┌┐└┘├┤┬┴┼─│':
                    text.append(char, style="cyan")

                # Full block - bright green (data bars)
                elif char == '█':
                    text.append(char, style="bright_green")

                # Block gradients - green shades
                elif char == '▓':
                    text.append(char, style="green")
                elif char == '▒':
                    text.append(char, style="green")
                elif char == '░':
                    text.append(char, style="green")

                # Numbers - bright yellow
                elif char.isdigit():
                    text.append(char, style="bright_yellow")

                # Percent, dollar, hash - bright magenta
                elif char in '%$#':
                    text.append(char, style="bright_magenta")

                # Letters - white
                elif char.isalpha():
                    text.append(char, style="white")

                # Everything else - white
                else:
                    text.append(char, style="white")

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def colorize_line(self, line: str, line_idx: int, is_incomplete: bool = False) -> Text:
        """
        Colorize a single line (for progressive rendering).

        Args:
            line: Single line of text
            line_idx: Line number
            is_incomplete: Whether line is still being generated

        Returns:
            Rich Text with colors
        """
        # Strip color hints if present in the line (shouldn't happen during streaming, but just in case)
        if "###COLORS###" in line:
            line = line.split("###COLORS###")[0]

        # Colorize the line using mode-specific method
        if self.mode == "diagram":
            colored = self._colorize_diagram(line)
        elif self.mode == "chart":
            colored = self._colorize_chart(line)
        else:
            colored = self._colorize_art(line)

        # If incomplete, dim all the colors
        if is_incomplete:
            dim_text = Text()
            for span in colored._spans:
                style = span.style if span.style else "white"
                dim_text.append(
                    colored.plain[span.start:span.end],
                    style=f"dim {style}"
                )
            return dim_text

        return colored
