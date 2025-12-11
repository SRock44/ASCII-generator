"""AI-powered intelligent ASCII art colorization."""
from typing import Optional, Dict, Set
from rich.text import Text
import re


class ASCIIColorizer:
    """
    AI-powered colorizer that uses color hints from the AI model.
    Prioritizes AI-provided colors over hardcoded rules.
    """

    def __init__(self, prompt: str = "", mode: str = "art"):
        """
        Initialize colorizer.

        Args:
            prompt: User's original prompt
            mode: Generation mode ('art', 'chart', 'diagram')
        """
        self.mode = mode
        self.color_hints = {}  # Feature-based: {'outline': 'bright_cyan', ...}
        self.char_colors = {}  # Character-based: {'/': 'bright_cyan', 'o': 'bright_yellow', ...}
        self.region_colors = {}  # Region-based: {'top': 'orange', 'middle': 'yellow', ...}
        self.default_color = None  # Default color if specified

    def _normalize_color(self, color: str) -> str:
        """
        Normalize color value to Rich-compatible format.
        Supports:
        - Named colors: "red", "bright_cyan", etc.
        - RGB: "rgb(255,0,0)" or "rgb(255, 0, 0)"
        - HEX: "#ff0000" or "#FF0000" or "ff0000"
        
        Args:
            color: Color value from AI (can be named, RGB, or HEX)
            
        Returns:
            Normalized color string for Rich
        """
        color = color.strip()
        
        # Check if it's already a valid named color (Rich will validate)
        # Common named colors that Rich supports
        named_colors = [
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white',
            'orange', 'brown', 'grey', 'gray'
        ]
        
        if color.lower() in named_colors:
            return color.lower()
        
        # Check for RGB format: rgb(255,0,0) or rgb(255, 0, 0)
        rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color, re.IGNORECASE)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            # Validate RGB values (0-255)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            return f"rgb({r},{g},{b})"
        
        # Check for HEX format: #ff0000 or ff0000
        hex_match = re.match(r'#?([0-9a-fA-F]{6})', color)
        if hex_match:
            hex_value = hex_match.group(1)
            return f"#{hex_value}"
        
        # Check for short HEX: #f00 or f00
        short_hex_match = re.match(r'#?([0-9a-fA-F]{3})', color)
        if short_hex_match:
            hex_value = short_hex_match.group(1)
            # Expand short hex to full hex
            r = hex_value[0] * 2
            g = hex_value[1] * 2
            b = hex_value[2] * 2
            return f"#{r}{g}{b}"
        
        # If it doesn't match any format, return as-is (Rich might handle it)
        # or fall back to a safe default
        return color

    def parse_color_hints(self, content: str) -> str:
        """
        Extract color hints from AI output and return clean ASCII art.
        Supports multiple formats:
        - Feature-based: "outline: bright_cyan"
        - Character-based: "char /: bright_cyan" or "char o: bright_yellow"
        - Region-based: "region top: orange" or "region middle: yellow"
        - Default: "default: white"

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
                line = line.strip()
                if not line or ":" not in line:
                    continue
                
                key, color = line.split(":", 1)
                key = key.strip().lower()
                color = color.strip()
                
                # Parse different formats
                if key.startswith("char "):
                    # Character-based: "char /: bright_cyan"
                    char = key[5:].strip()
                    if len(char) == 1:
                        self.char_colors[char] = self._normalize_color(color)
                elif key.startswith("region "):
                    # Region-based: "region top: orange"
                    region = key[7:].strip()
                    self.region_colors[region] = self._normalize_color(color)
                elif key == "default":
                    # Default color
                    self.default_color = self._normalize_color(color)
                else:
                    # Feature-based: "outline: bright_cyan"
                    self.color_hints[key] = self._normalize_color(color)

        return ascii_art

    def _get_color_for_char(self, char: str, line_idx: int, total_lines: int, 
                           char_type: str = None) -> str:
        """
        Get color for a character, prioritizing AI-provided colors.
        
        Priority order:
        1. Character-specific color from AI (char_colors)
        2. Feature-based color from AI (color_hints)
        3. Region-based color from AI (region_colors)
        4. Default color from AI
        5. Mode-specific hardcoded defaults
        
        Args:
            char: Character to colorize
            line_idx: Current line index
            total_lines: Total number of non-empty lines
            char_type: Optional character type hint (e.g., 'outline', 'eyes', 'body')
            
        Returns:
            Color name as string
        """
        # 1. Check character-specific color from AI
        if char in self.char_colors:
            return self.char_colors[char]
        
        # 2. Check feature-based color from AI
        if char_type and char_type in self.color_hints:
            return self.color_hints[char_type]
        
        # 3. Check region-based color from AI
        if total_lines > 0:
            region_ratio = line_idx / total_lines if total_lines > 0 else 0
            if region_ratio < 0.25:
                if 'top' in self.region_colors:
                    return self.region_colors['top']
            elif region_ratio < 0.75:
                if 'middle' in self.region_colors:
                    return self.region_colors['middle']
            else:
                if 'bottom' in self.region_colors:
                    return self.region_colors['bottom']
        
        # 4. Check default color from AI
        if self.default_color:
            return self.default_color
        
        # 5. Fall back to None (will use mode-specific defaults)
        return None

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
        Prioritizes AI-provided colors over hardcoded rules.

        Args:
            content: ASCII art content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        total_lines = len(non_empty_lines)

        # Get AI colors with fallbacks
        outline_color = self.color_hints.get('outline')
        eyes_color = self.color_hints.get('eyes')
        nose_color = self.color_hints.get('nose')
        mouth_color = self.color_hints.get('mouth')
        body_color = self.color_hints.get('body')
        hat_color = self.color_hints.get('hat')
        ears_color = self.color_hints.get('ears')

        # Fallback defaults (only if AI didn't provide)
        if not outline_color:
            outline_color = 'bright_cyan'
        if not eyes_color:
            eyes_color = 'bright_yellow'
        if not nose_color:
            nose_color = 'bright_green'
        if not mouth_color:
            mouth_color = 'bright_green'
        if not body_color:
            body_color = 'white'
        if not hat_color:
            hat_color = 'brown'
        if not ears_color:
            ears_color = outline_color

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            # Detect region
            non_empty_idx = sum(1 for i in range(line_idx) if lines[i].strip())
            is_top = non_empty_idx < total_lines * 0.25 if total_lines > 0 else False

            for char in line:
                # Try to get color from AI first
                ai_color = self._get_color_for_char(char, non_empty_idx, total_lines)
                
                if ai_color:
                    # Use AI-provided color
                    text.append(char, style=ai_color)
                else:
                    # Fall back to character-type based coloring
                    # Structural outlines
                    if char in '/\\|_-=+':
                        color = hat_color if is_top and 'hat' in self.color_hints else outline_color
                        text.append(char, style=color)
                    # Eyes
                    elif char in 'oO@':
                        text.append(char, style=eyes_color)
                    # Nose/mouth features
                    elif char in '<>v^':
                        text.append(char, style=nose_color)
                    # Solid blocks
                    elif char in '#█▓▒░':
                        text.append(char, style=body_color)
                    # Dots and stars
                    elif char in '.*':
                        text.append(char, style="bright_magenta")
                    # Parentheses and brackets
                    elif char in '(){}[]':
                        text.append(char, style="cyan")
                    # Everything else
                    else:
                        text.append(char, style=body_color)

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def _colorize_diagram(self, content: str) -> Text:
        """
        Colorize diagrams using AI-suggested colors with smart fallbacks.
        Prioritizes AI-provided colors over hardcoded rules.

        Args:
            content: Diagram content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        total_lines = len(non_empty_lines)

        # Get AI colors with fallbacks
        box_corner_color = self.color_hints.get('box_corners') or self.color_hints.get('corners')
        box_line_color = self.color_hints.get('box_lines') or self.color_hints.get('lines')
        arrow_color = self.color_hints.get('arrows')
        text_color = self.color_hints.get('text') or self.color_hints.get('labels')
        default_diagram_color = self.color_hints.get('default')

        # Fallback defaults (only if AI didn't provide)
        if not box_corner_color:
            box_corner_color = 'bright_blue'
        if not box_line_color:
            box_line_color = 'cyan'
        if not arrow_color:
            arrow_color = 'bright_yellow'
        if not text_color:
            text_color = 'bright_white'
        if not default_diagram_color:
            default_diagram_color = 'white'

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            non_empty_idx = sum(1 for i in range(line_idx) if lines[i].strip())

            for char in line:
                # Try to get color from AI first
                ai_color = self._get_color_for_char(char, non_empty_idx, total_lines)
                
                if ai_color:
                    # Use AI-provided color
                    text.append(char, style=ai_color)
                else:
                    # Fall back to character-type based coloring
                    # Box corners
                    if char in '┌┐└┘├┤┬┴┼':
                        text.append(char, style=box_corner_color)
                    # Box lines
                    elif char in '─│':
                        text.append(char, style=box_line_color)
                    # Arrows
                    elif char in '→←↑↓':
                        text.append(char, style=arrow_color)
                    # Letters and numbers
                    elif char.isalnum():
                        text.append(char, style=text_color)
                    # Everything else
                    else:
                        text.append(char, style=default_diagram_color)

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def _colorize_chart(self, content: str) -> Text:
        """
        Colorize charts using AI-suggested colors with smart fallbacks.
        Prioritizes AI-provided colors over hardcoded rules.

        Args:
            content: Chart content

        Returns:
            Rich Text with colors
        """
        text = Text()
        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        total_lines = len(non_empty_lines)

        # Get AI colors with fallbacks
        box_color = self.color_hints.get('box') or self.color_hints.get('borders')
        bar_color = self.color_hints.get('bars') or self.color_hints.get('data')
        number_color = self.color_hints.get('numbers') or self.color_hints.get('values')
        symbol_color = self.color_hints.get('symbols')
        label_color = self.color_hints.get('labels') or self.color_hints.get('text')
        default_chart_color = self.color_hints.get('default')

        # Fallback defaults (only if AI didn't provide)
        if not box_color:
            box_color = 'cyan'
        if not bar_color:
            bar_color = 'bright_green'
        if not number_color:
            number_color = 'bright_yellow'
        if not symbol_color:
            symbol_color = 'bright_magenta'
        if not label_color:
            label_color = 'white'
        if not default_chart_color:
            default_chart_color = 'white'

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx < len(lines) - 1:
                    text.append("\n")
                continue

            non_empty_idx = sum(1 for i in range(line_idx) if lines[i].strip())

            for char in line:
                # Try to get color from AI first
                ai_color = self._get_color_for_char(char, non_empty_idx, total_lines)
                
                if ai_color:
                    # Use AI-provided color
                    text.append(char, style=ai_color)
                else:
                    # Fall back to character-type based coloring
                    # Box drawing
                    if char in '┌┐└┘├┤┬┴┼─│':
                        text.append(char, style=box_color)
                    # Full block (data bars)
                    elif char == '█':
                        text.append(char, style=bar_color)
                    # Block gradients
                    elif char in '▓▒░':
                        text.append(char, style=bar_color)
                    # Numbers
                    elif char.isdigit():
                        text.append(char, style=number_color)
                    # Percent, dollar, hash
                    elif char in '%$#':
                        text.append(char, style=symbol_color)
                    # Letters
                    elif char.isalpha():
                        text.append(char, style=label_color)
                    # Everything else
                    else:
                        text.append(char, style=default_chart_color)

            if line_idx < len(lines) - 1:
                text.append("\n")

        return text

    def colorize_line(self, line: str, line_idx: int, is_incomplete: bool = False, accumulated_content: str = "") -> Text:
        """
        Colorize a single line (for progressive rendering).
        Can parse color hints from accumulated content if provided.

        Args:
            line: Single line of text
            line_idx: Line number
            is_incomplete: Whether line is still being generated
            accumulated_content: Optional full accumulated content (for parsing color hints during streaming)

        Returns:
            Rich Text with colors
        """
        # If accumulated content is provided, try to parse color hints from it
        # This allows color hints to be used during streaming once they're available
        if accumulated_content and "###COLORS###" in accumulated_content:
            # Parse color hints from accumulated content (this will update self.color_hints, etc.)
            self.parse_color_hints(accumulated_content)
        
        # Strip color hints if present in the line itself
        if "###COLORS###" in line:
            line = line.split("###COLORS###")[0]
            # Also parse hints from this line
            self.parse_color_hints(line + "\n###COLORS###")

        # Create a temporary single-line content for colorization
        # We'll use the full colorize method but with just this line
        # The color hints should already be parsed if available
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
