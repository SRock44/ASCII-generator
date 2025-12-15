"""Validators for ASCII art strictness enforcement."""
from typing import Tuple, List, Optional
from collections import Counter
import re


class ValidationResult:
    """Result of validation check."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        """
        Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: Optional list of error messages
            warnings: Optional list of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []

    def __bool__(self):
        """Return validation status."""
        return self.is_valid


class ASCIIValidator:
    """Validator for ASCII art generation strictness."""

    # Character whitelists for different generation types
    ASCII_ART_CHARS = set(
        # Basic ASCII printables (excluding control chars)
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    )
    
    LOGO_CHARS = set(
        # Basic ASCII printables
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        # Block characters for bold text and borders
        "█░▒▓"
    )

    CHART_CHARS = set(
        # Box-drawing characters
        "─│┌┐└┘├┤┬┴┼"
        # Block characters
        "█▓▒░"
        # Basic alphanumerics and symbols
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " .,:-+%$#@()[]"
    )

    DIAGRAM_CHARS = set(
        # Box-drawing characters (complete set)
        "┌┐└┘─│├┤┬┴┼"
        # Arrows
        "→←↑↓"
        # Alphanumerics and basic symbols
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " .,:-_/()"
    )

    def __init__(self, mode: str = "art"):
        """
        Initialize validator.

        Args:
            mode: Validation mode - "art", "chart", "diagram", or "logo"
        """
        self.mode = mode.lower()

        # Select character whitelist based on mode
        if self.mode == "chart":
            self.allowed_chars = self.CHART_CHARS
            self.max_lines = 30
            self.max_width = 80
        elif self.mode == "diagram":
            self.allowed_chars = self.DIAGRAM_CHARS
            self.max_lines = 50
            self.max_width = 80
        elif self.mode == "logo":
            # Logo mode allows larger sizes for branding and text art
            self.allowed_chars = self.LOGO_CHARS
            self.max_lines = 100
            self.max_width = 150
        else:  # Default to art mode
            self.allowed_chars = self.ASCII_ART_CHARS
            self.max_lines = 20  # ascii-art.de style: 4-12 ideal, max 20
            self.max_width = 80

    def validate(self, content: str, strict: bool = False) -> ValidationResult:
        """
        Validate ASCII content against strictness rules.

        Args:
            content: ASCII content to validate
            strict: Whether to enforce strict rules (returns invalid on warnings)

        Returns:
            ValidationResult with status and error/warning messages
        """
        errors = []
        warnings = []

        if not content or not content.strip():
            errors.append("Content is empty")
            return ValidationResult(False, errors, warnings)

        lines = content.split("\n")
        
        # Check for incomplete/cut-off art (common issue)
        if self.mode == "art" and len(lines) >= 3:
            non_empty_lines = [line for line in lines if line.strip()]
            if non_empty_lines:
                # Check if last line looks incomplete (ends with incomplete pattern)
                last_line = non_empty_lines[-1].strip()
                # Incomplete patterns: trailing backslashes, incomplete brackets, cut-off lines
                incomplete_patterns = [
                    last_line.endswith('\\') and len(last_line) < 5,  # Single trailing backslash
                    last_line.endswith('/') and len(last_line) < 5,  # Single trailing slash
                    last_line.endswith('|') and len(last_line) < 5,  # Single trailing pipe
                    last_line.endswith('_') and len(last_line) < 5,  # Single trailing underscore
                    last_line.count('(') != last_line.count(')'),  # Unmatched parentheses
                    last_line.count('[') != last_line.count(']'),  # Unmatched brackets
                    last_line.count('{') != last_line.count('}'),  # Unmatched braces
                ]
                # Also check if last line is much shorter than previous lines (likely cut off)
                if len(non_empty_lines) >= 2:
                    prev_line_len = len(non_empty_lines[-2].strip())
                    if len(last_line) < prev_line_len * 0.3 and prev_line_len > 10:
                        incomplete_patterns.append(True)
                
                if any(incomplete_patterns):
                    errors.append("Art appears incomplete or cut off - ensure the drawing is complete")

        # 1. Check line count
        if len(lines) > self.max_lines:
            errors.append(f"Exceeds maximum {self.max_lines} lines (has {len(lines)} lines)")

        # 2. Check character whitelist
        invalid_chars = set()
        for line in lines:
            for char in line:
                if char not in self.allowed_chars and char != '\n':
                    invalid_chars.add(char)

        if invalid_chars:
            char_list = ', '.join(f"'{c}' (U+{ord(c):04X})" for c in sorted(invalid_chars))
            errors.append(f"Contains disallowed characters: {char_list}")

        # 3. Check line width
        lines_too_wide = []
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_width:
                lines_too_wide.append((i, len(line)))

        if lines_too_wide:
            details = ', '.join(f"line {i}: {w} chars" for i, w in lines_too_wide[:3])
            errors.append(f"Lines exceed maximum width of {self.max_width} chars: {details}")

        # 4. Check alignment consistency (all non-empty lines should have same leading spaces)
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            leading_spaces = [len(line) - len(line.lstrip()) for line in non_empty_lines]
            unique_leading = set(leading_spaces)

            if len(unique_leading) > 1:
                warnings.append(
                    f"Inconsistent alignment: found {len(unique_leading)} different indentation levels "
                    f"(expected all lines to have same leading spaces)"
                )

        # 5. Check for trailing whitespace
        lines_with_trailing = []
        for i, line in enumerate(lines, 1):
            if line and line != line.rstrip():
                lines_with_trailing.append(i)

        if lines_with_trailing:
            count = len(lines_with_trailing)
            warnings.append(f"Found trailing whitespace on {count} line(s)")

        # 6. Check for markdown artifacts
        if content.strip().startswith("```") or content.strip().endswith("```"):
            errors.append("Contains markdown code block artifacts (```) - should be pure ASCII")

        # 7. Check for explanatory text (heuristic: lines that look like sentences)
        explanation_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Detect lines that look like explanations (complete sentences, no ASCII art patterns)
            if stripped and len(stripped) > 40:
                # Check if it looks like prose (has many words)
                words = stripped.split()
                if len(words) > 6 and not any(c in stripped for c in "│─┌┐└┘█▓▒░"):
                    # Likely an explanation
                    explanation_lines.append(i)

        if explanation_lines and len(explanation_lines) > 2:
            warnings.append(f"May contain explanatory text instead of pure ASCII art")

        # 8. Quality check: Ensure output is recognizable and not just repetitive patterns
        if self.mode == "art":
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if len(non_empty_lines) >= 3:
                normalized_lines = [''.join(line.split()) for line in non_empty_lines]
                total_lines = len(normalized_lines)

                # LINE COUNT CHECK - Very lenient (only error on extreme cases)
                if total_lines > 75:  # Only error on truly excessive lines
                    errors.append(
                        f"Too many lines ({total_lines}) - art is extremely long."
                    )
                # No warnings for line count - let the AI create what it wants

                # CONSECUTIVE REPETITION CHECK - Very lenient (only error on extreme repetition)
                consecutive_count = 1
                max_consecutive = 1
                for i in range(1, len(normalized_lines)):
                    if normalized_lines[i] == normalized_lines[i-1] and normalized_lines[i]:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 1

                # Only error on extreme repetition (10+ consecutive identical lines)
                if max_consecutive > 10:
                    errors.append(
                        f"Extreme repetition detected: {max_consecutive} consecutive identical lines."
                    )
                # No warnings for repetition - allow legitimate patterns

                # TOTAL PATTERN REPETITION - Very lenient (only error on extreme cases)
                pattern_counts = Counter(normalized_lines)
                max_pattern_count = max(pattern_counts.values()) if pattern_counts else 0

                # Only error if a pattern appears 15+ times (extreme repetition)
                if max_pattern_count >= 15:
                    most_common = pattern_counts.most_common(1)[0]
                    errors.append(
                        f"Extreme pattern repetition: '{most_common[0][:15]}' appears {most_common[1]} times."
                    )
                # No warnings for pattern repetition

                # DEGENERATE "LADDER/TEMPLATE" DETECTION (cheap, UX-focused)
                # If most lines collapse to the same non-space structure, it's usually not a drawing.
                # This catches outputs like the "dragon" example that is just repeated scaffolding.
                if total_lines >= 10 and pattern_counts:
                    max_fraction = max_pattern_count / total_lines if total_lines else 0
                    # Require a strong majority to avoid false positives on legitimate patterns.
                    if max_pattern_count >= 8 and max_fraction >= 0.75:
                        errors.append(
                            "Output appears to repeat the same line structure too many times (degenerate template/ladder)."
                        )

                # DENSITY CHECK - Very lenient (only error on extreme density)
                original_lines = [line for line in lines if line.strip()]
                all_chars = ''.join(original_lines)
                spaces = all_chars.count(' ')
                total_chars = len(all_chars)
                filled_ratio = (total_chars - spaces) / total_chars if total_chars > 0 else 0

                # Only error on extreme density (>90% filled - likely broken)
                if filled_ratio > 0.90:
                    errors.append(
                        f"Extremely dense ({int(filled_ratio * 100)}% filled) - likely broken output."
                    )
                # No warnings for density - allow any reasonable density

                # Removed all quality warnings - let the AI create what it wants
                # No checks for iconic features, structural variety, or symmetry
                # These are artistic choices, not validation errors

        # 8.5. Check for duplicate content in boxes (diagram mode)
        if self.mode == "diagram":
            # Check for duplicate lines within boxes
            in_box = False
            box_lines = []
            for i, line in enumerate(lines):
                if "┌" in line and "┐" in line:
                    in_box = True
                    box_lines = []
                elif "└" in line and "┘" in line:
                    if in_box and box_lines:
                        # Check for duplicates in this box
                        content_lines = [l.split("│")[1:-1] if "│" in l and l.count("│") >= 2 else [l.strip()] for l in box_lines if "│" in l]
                        normalized = [''.join(c).strip().lower() for c in content_lines if c]
                        if len(normalized) != len(set(normalized)):
                            warnings.append("Box contains duplicate content lines - each line should be unique")
                    in_box = False
                    box_lines = []
                elif in_box and "│" in line:
                    box_lines.append(line)

        # 9. Mode-specific validations
        if self.mode == "diagram":
            # Check for complete box structures
            has_box_chars = any(c in content for c in "┌┐└┘─│")
            if has_box_chars:
                # Check for boxes with all 4 corners
                if "┌" in content or "┐" in content or "└" in content or "┘" in content:
                    corner_counts = {
                        "┌": content.count("┌"),
                        "┐": content.count("┐"),
                        "└": content.count("└"),
                        "┘": content.count("┘")
                    }
                    # Boxes should have matching corners - every top corner needs a bottom corner
                    if not (corner_counts["┌"] == corner_counts["└"] and
                            corner_counts["┐"] == corner_counts["┘"]):
                        errors.append(
                            f"Incomplete box structures: {corner_counts['┌']} top-left corners but {corner_counts['└']} bottom-left, "
                            f"{corner_counts['┐']} top-right but {corner_counts['┘']} bottom-right. "
                            "Every box must have all 4 corners complete."
                        )
                    
                    # Check for arrows inside boxes (should be between boxes)
                    lines = content.split("\n")
                    arrow_chars = "→←↑↓"
                    for i, line in enumerate(lines):
                        if any(c in line for c in arrow_chars):
                            # Check if this line looks like it's inside a box (has │ on both sides)
                            if "│" in line:
                                # Count │ characters - if there are │ on both sides, arrow might be inside box
                                parts = line.split("│")
                                if len(parts) > 2:  # Has │ on both sides
                                    # Check if arrow is between │ characters (inside box)
                                    for part in parts[1:-1]:  # Middle parts (between │)
                                        if any(c in part for c in arrow_chars):
                                            warnings.append(
                                                f"Arrow found inside box on line {i+1}. Arrows should be between boxes, not inside them."
                                            )

        # Determine if valid
        is_valid = len(errors) == 0
        if strict and warnings:
            # In strict mode, warnings also fail validation
            is_valid = False
        
        # For art mode, also fail if quality warnings indicate broken output
        if self.mode == "art" and not is_valid:
            # If we have quality errors, mark as invalid
            quality_errors = [e for e in errors if "broken" in e.lower() or "repetitive" in e.lower()]
            if quality_errors:
                is_valid = False

        return ValidationResult(is_valid, errors, warnings)

    def clean(self, content: str) -> str:
        """
        Clean and fix common issues in ASCII content.

        Args:
            content: ASCII content to clean

        Returns:
            Cleaned content
        """
        if not content:
            return content

        # NOTE: Do NOT strip color hints here - the colorizer needs them to parse colors
        # Color hints will be stripped in the renderer after colorizer has parsed them

        # Normalize newlines but DO NOT strip leading spaces.
        # Leading indentation is part of ASCII art and must be preserved.
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove markdown code fences AGGRESSIVELY (common LLM artifact),
        # but preserve indentation on all other lines.
        lines = content.split("\n")
        lines = [line for line in lines if not line.lstrip().startswith("```")]

        # Remove leading/trailing completely blank lines (not spaces on content lines).
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        content = "\n".join(lines)
        lines = content.split("\n") if content else []

        # Remove trailing whitespace from all lines (safe for alignment)
        lines = [line.rstrip() for line in lines]

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Remove repetitive pattern lines (like | | repeated 50 times)
        # For art mode, be VERY conservative - only remove extreme repetition (15+ times)
        # For charts, be lenient - pie charts and bar charts can have legitimate repetition
        if self.mode == "art":
            # Only remove EXTREME repetition (15+ identical lines) - let validation catch moderate issues
            lines = self._remove_repetitive_patterns_conservative(lines)
        elif self.mode == "chart":
            # Charts can have repetitive patterns (pie chart slices, bar chart rows)
            # Only remove EXTREME repetition (15+ identical lines)
            lines = self._remove_repetitive_patterns_conservative(lines)
        else:
            lines = self._remove_repetitive_patterns(lines)

        # Fix alignment - PRESERVE STRUCTURE for art mode
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            leading_spaces = [len(line) - len(line.lstrip()) for line in non_empty_lines]
            min_indent = min(leading_spaces)
            max_indent = max(leading_spaces)
            indent_range = max_indent - min_indent

            if self.mode == "art":
                # For art: do NOT shift lines left (can destroy drawings).
                # We only do a SAFE fix: pad a small number of under-indented outlier lines
                # up to the dominant indentation. This fixes cases like a top line being flush
                # left while the rest of the drawing is indented.
                lines = self._pad_underindented_outliers(lines)
            else:
                # For charts/diagrams: Normalize alignment (they should be aligned)
                if indent_range > 0:
                    fixed_lines = []
                    for line in lines:
                        if line.strip():
                            # Normalize to minimum indent
                            fixed_lines.append(" " * min_indent + line.lstrip())
                        else:
                            fixed_lines.append("")
                    lines = fixed_lines

        # Remove invalid characters (replace with space or remove)
        cleaned_lines = []
        for line in lines:
            cleaned_line = ""
            for char in line:
                if char in self.allowed_chars or char == '\n':
                    cleaned_line += char
                else:
                    # Replace invalid chars with space (preserve structure)
                    cleaned_line += " "
            cleaned_lines.append(cleaned_line)
        lines = cleaned_lines

        # Truncate to max lines (but ensure we don't cut off box borders)
        if len(lines) > self.max_lines:
            # Check if last few lines might be box borders
            if self.mode in ["chart", "diagram"]:
                # Look for closing box border in last 3 lines
                has_closing_border = False
                for i in range(max(0, len(lines) - 3), len(lines)):
                    if any(char in lines[i] for char in ["└", "┘", "─"]):
                        has_closing_border = True
                        break

                if has_closing_border:
                    # Keep a bit more to preserve the closing border
                    lines = lines[:min(self.max_lines + 2, len(lines))]
                else:
                    lines = lines[:self.max_lines]
            else:
                lines = lines[:self.max_lines]

        # Normalize box widths - ensure all lines in a box have the same width
        if self.mode in ["chart", "diagram"]:
            lines = self._normalize_box_widths(lines)
            # Complete any incomplete boxes (add missing bottom borders)
            lines = self._complete_incomplete_boxes(lines)
            # Remove duplicate content in boxes (common issue in architecture diagrams)
            lines = self._remove_duplicate_box_content(lines)
            # Fix arrow alignment - align arrows with connection points
            lines = self._fix_arrow_alignment(lines)

        # Truncate lines to max width (but don't cut box borders)
        truncated_lines = []
        for line in lines:
            if len(line) > self.max_width:
                # Check if this looks like a box line
                if self.mode in ["chart", "diagram"] and any(char in line for char in ["│", "┤", "┘", "└"]):
                    # Don't truncate box lines - keep them intact
                    truncated_lines.append(line)
                else:
                    truncated_lines.append(line[:self.max_width])
            else:
                truncated_lines.append(line)
        lines = truncated_lines

        return "\n".join(lines)

    def clean_minimal(self, content: str) -> str:
        """
        Minimal cleaning - only removes markdown and trailing spaces.
        Preserves original structure and alignment.

        Args:
            content: ASCII content to clean

        Returns:
            Minimally cleaned content
        """
        if not content:
            return content

        # Normalize newlines but DO NOT strip leading spaces (indentation is meaningful).
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove markdown code fences (``` / ```ascii / etc.) while preserving indentation elsewhere.
        lines = content.split("\n")
        lines = [line for line in lines if not line.lstrip().startswith("```")]

        # Remove leading/trailing completely blank lines.
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        # Only remove trailing whitespace from lines (preserve leading spaces for structure)
        lines = [line.rstrip() for line in lines]

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Safe art-only alignment fix (pads a few under-indented outlier lines).
        # This improves UX in streamed output without risking destructive shifts.
        if self.mode == "art":
            lines = self._pad_underindented_outliers(lines)

        # That's it - preserve everything else (alignment, structure, etc.)
        return "\n".join(lines)

    def _pad_underindented_outliers(self, lines: List[str]) -> List[str]:
        """
        Pad a small number of under-indented outlier lines to the dominant indentation.
        Never removes leading spaces; only adds them.

        This fixes common LLM artifacts where a single line (often the first) is flush-left
        while the rest of the drawing is indented.
        """
        if not lines:
            return lines

        non_empty_indices = [i for i, l in enumerate(lines) if l.strip()]
        if len(non_empty_indices) < 4:
            return lines

        indents = [len(lines[i]) - len(lines[i].lstrip()) for i in non_empty_indices]
        indent_counts = Counter(indents)
        dominant_indent, dominant_count = indent_counts.most_common(1)[0]

        # Only act when there's a clear dominant indentation that is meaningfully > 0.
        if dominant_indent < 2:
            return lines
        if (dominant_count / len(non_empty_indices)) < 0.60:
            return lines

        # Consider under-indented lines as outliers if they're notably smaller than dominant.
        outliers = []
        for i in non_empty_indices:
            ci = len(lines[i]) - len(lines[i].lstrip())
            if ci < (dominant_indent - 2):
                outliers.append(i)

        # If too many lines are "outliers", it may be intentional structure; do nothing.
        if not outliers:
            return lines
        if (len(outliers) / len(non_empty_indices)) > 0.25:
            return lines

        fixed = list(lines)
        for i in outliers:
            line = fixed[i]
            ci = len(line) - len(line.lstrip())
            pad = dominant_indent - ci
            if pad > 0:
                fixed[i] = (" " * pad) + line
        return fixed

    def _normalize_box_widths(self, lines: List[str]) -> List[str]:
        """
        Normalize box widths - ensure all lines within a box have equal width.
        Simple approach: find consecutive box lines and make them all the same width.

        Args:
            lines: List of lines

        Returns:
            List of lines with normalized box widths
        """
        if not lines:
            return lines

        normalized = []
        box_group = []

        for i, line in enumerate(lines):
            # Check if this line is part of a box (contains box-drawing characters)
            is_box_line = any(c in line for c in ["┌", "┐", "└", "┘", "│", "┬", "┴", "├", "┤"])

            if is_box_line:
                box_group.append(line)
            else:
                # End of box group - normalize it
                if box_group:
                    normalized.extend(self._pad_box_group(box_group))
                    box_group = []
                normalized.append(line)

        # Handle remaining box group
        if box_group:
            normalized.extend(self._pad_box_group(box_group))

        return normalized

    def _complete_incomplete_boxes(self, lines: List[str]) -> List[str]:
        """
        Complete any boxes that are missing their bottom border.
        Detects boxes that start with ┌ but don't have a corresponding └─┘ bottom border.
        
        Args:
            lines: List of lines
            
        Returns:
            List of lines with incomplete boxes completed
        """
        if not lines:
            return lines
        
        completed = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a box (has ┌)
            if "┌" in line:
                # Find the box group
                box_start = i
                box_lines = []
                found_bottom = False
                
                # Collect all lines that are part of this box
                j = i
                while j < len(lines):
                    current_line = lines[j]
                    box_lines.append(current_line)
                    
                    # Check if this line has a bottom border
                    if "└" in current_line and "┘" in current_line:
                        found_bottom = True
                        j += 1
                        break
                    
                    # Check if we've left the box (next line doesn't have │ or box chars)
                    if j + 1 < len(lines):
                        next_line = lines[j + 1]
                        # If next line doesn't have │ and doesn't start a new box, we've left this box
                        if "│" not in next_line and "┌" not in next_line and next_line.strip():
                            # We've left the box without finding bottom border
                            break
                    
                    j += 1
                
                # If box doesn't have a bottom border, add it
                if not found_bottom and box_lines:
                    # Find the width of the box (from top border)
                    top_line = box_lines[0]
                    # Find positions of ┌ and ┐
                    left_pos = top_line.find("┌")
                    right_pos = top_line.rfind("┐")
                    
                    if left_pos >= 0 and right_pos > left_pos:
                        # Calculate width
                        box_width = right_pos - left_pos
                        # Create bottom border
                        bottom_border = " " * left_pos + "└" + "─" * (box_width - 1) + "┘"
                        box_lines.append(bottom_border)
                
                # Add all box lines to completed
                completed.extend(box_lines)
                i = j
            else:
                completed.append(line)
                i += 1
        
        return completed

    def _remove_repetitive_patterns(self, lines: List[str]) -> List[str]:
        """
        Remove repetitive pattern lines that indicate the AI got stuck.
        Only removes when we detect EXCESSIVE repetition (5+ times), not legitimate structure.

        Distinguishes between:
        - Legitimate structure: Same line 2-4 times (body parts, etc.)
        - Stuck pattern: Same line 5+ times (AI error)

        Args:
            lines: List of lines

        Returns:
            List of lines with excessive repetitive patterns removed
        """
        if not lines:
            return lines

        cleaned = []
        last_line_normalized = None
        repeat_count = 1
        # STRICT: Quality-focused thresholds to prevent broken output
        # Simple patterns (1-2 unique chars, ≤3 total): max 4 occurrences
        # Complex patterns: max 5 occurrences
        # This ensures variety and prevents stuck loops

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                if cleaned:
                    cleaned.append(line)
                continue

            # Normalize line for pattern detection (remove spacing variations)
            line_normalized = ''.join(line_stripped.split())

            # Determine threshold based on pattern complexity
            unique_chars = len(set(line_normalized))
            pattern_length = len(line_normalized)
            
            # Simple patterns: very short (≤3 chars) with 1-2 unique characters
            is_simple_pattern = (
                pattern_length <= 3 and 
                unique_chars <= 2
            )
            
            if is_simple_pattern:
                # Simple patterns like "| |", "||", "/ /" - max 4 occurrences
                threshold = 4
            else:
                # Complex patterns - max 5 occurrences
                threshold = 5

            # Detect repetitive patterns
            if last_line_normalized and line_normalized == last_line_normalized:
                repeat_count += 1
                if repeat_count <= threshold:
                    cleaned.append(line)
                else:
                    # Skip excessive repetition but continue processing - don't break entirely
                    # This allows the rest of the content to be preserved
                    # The validator will catch this and trigger a retry
                    continue
            else:
                repeat_count = 1
                last_line_normalized = line_normalized
                cleaned.append(line)

        # Final cleanup: remove trailing empty lines
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        return cleaned

    def _remove_repetitive_patterns_conservative(self, lines: List[str]) -> List[str]:
        """
        Remove repetitive patterns conservatively for art mode.
        Only removes EXTREME repetition (15+ identical lines), preserving legitimate structure.
        
        Args:
            lines: List of lines
            
        Returns:
            List of lines with only extreme repetitive patterns removed
        """
        if not lines:
            return lines

        cleaned = []
        last_line_normalized = None
        repeat_count = 1
        # Very conservative: only remove if 15+ identical lines (was 10)
        max_allowed_occurrences = 15

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                if cleaned:
                    cleaned.append(line)
                continue

            # Normalize line for pattern detection (remove spacing variations)
            line_normalized = ''.join(line_stripped.split())

            # Detect repetitive patterns
            if last_line_normalized and line_normalized == last_line_normalized:
                repeat_count += 1
                if repeat_count <= max_allowed_occurrences:
                    cleaned.append(line)
                else:
                    # Skip only the excessive repetitions, but keep scanning for subsequent unique lines.
                    # Breaking here can incorrectly truncate otherwise-valid content that follows.
                    continue
            else:
                repeat_count = 1
                last_line_normalized = line_normalized
                cleaned.append(line)

        # Final cleanup: remove trailing empty lines
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        return cleaned

    def _pad_box_group(self, box_lines: List[str]) -> List[str]:
        """
        Pad all lines in a box group to the same width.
        Finds the maximum line width and pads all lines to match.

        Args:
            box_lines: List of consecutive box lines

        Returns:
            Padded box lines
        """
        if not box_lines:
            return box_lines

        # Find maximum width
        max_width = max(len(line) for line in box_lines)

        padded = []
        for line in box_lines:
            if len(line) < max_width:
                stripped = line.rstrip()

                # Check what type of line this is
                if stripped.endswith("│"):
                    # Content line - pad before the │
                    last_bar_pos = stripped.rfind("│")
                    before_bar = line[:last_bar_pos]
                    padding_needed = max_width - len(line)
                    padded_line = before_bar + " " * padding_needed + "│"
                    padded.append(padded_line)

                elif "┌" in stripped and ("┐" in stripped or stripped.endswith("─")):
                    # Top border - pad with ─ instead of spaces
                    if stripped.endswith("┐"):
                        # Has closing corner, pad with ─ before it
                        before_corner = stripped[:-1]
                        padding_needed = max_width - len(stripped)
                        padded_line = before_corner + "─" * padding_needed + "┐"
                        padded.append(padded_line)
                    else:
                        # No closing corner yet, add ─ then ┐
                        padding_needed = max_width - len(stripped) - 1
                        padded_line = stripped + "─" * padding_needed + "┐"
                        padded.append(padded_line)

                elif "└" in stripped and ("┘" in stripped or stripped.endswith("─")):
                    # Bottom border - pad with ─ instead of spaces
                    if stripped.endswith("┘"):
                        # Has closing corner, pad with ─ before it
                        before_corner = stripped[:-1]
                        padding_needed = max_width - len(stripped)
                        padded_line = before_corner + "─" * padding_needed + "┘"
                        padded.append(padded_line)
                    else:
                        # No closing corner yet, add ─ then ┘
                        padding_needed = max_width - len(stripped) - 1
                        padded_line = stripped + "─" * padding_needed + "┘"
                        padded.append(padded_line)
                else:
                    # Other box lines - just pad at the end with spaces
                    padded.append(line + " " * (max_width - len(line)))
            else:
                padded.append(line)

        return padded

    def _remove_duplicate_box_content(self, lines: List[str]) -> List[str]:
        """
        Remove duplicate content lines within boxes.
        Common issue: AI repeats the same line twice in a box.
        
        Args:
            lines: List of lines
            
        Returns:
            List of lines with duplicate box content removed
        """
        if not lines:
            return lines
        
        cleaned = []
        in_box = False
        box_content = []
        box_start_idx = -1
        
        for i, line in enumerate(lines):
            # Check if this line starts a box
            if "┌" in line and "┐" in line:
                # Save any previous box content
                if in_box and box_content:
                    cleaned.extend(self._deduplicate_box_lines(box_content))
                    box_content = []
                
                in_box = True
                box_start_idx = i
                cleaned.append(line)
            # Check if this line ends a box
            elif "└" in line and "┘" in line:
                if in_box:
                    # Add deduplicated content
                    if box_content:
                        cleaned.extend(self._deduplicate_box_lines(box_content))
                        box_content = []
                    cleaned.append(line)
                    in_box = False
                else:
                    cleaned.append(line)
            # Check if this is a box content line (has │ on both sides)
            elif in_box and "│" in line:
                # Extract content (between │ characters)
                parts = line.split("│")
                if len(parts) >= 3:
                    content = "│".join(parts[1:-1]).strip()  # Content between first and last │
                    box_content.append((i, line, content))
                else:
                    cleaned.append(line)
            else:
                # Not in a box or not a box line
                if in_box and box_content:
                    # We left a box without seeing the bottom - flush content
                    cleaned.extend(self._deduplicate_box_lines(box_content))
                    box_content = []
                    in_box = False
                cleaned.append(line)
        
        # Handle any remaining box content
        if in_box and box_content:
            cleaned.extend(self._deduplicate_box_lines(box_content))
        
        return cleaned
    
    def _deduplicate_box_lines(self, box_content: List[tuple]) -> List[str]:
        """
        Remove duplicate content lines from box content.
        
        Args:
            box_content: List of (line_idx, full_line, content) tuples
            
        Returns:
            List of deduplicated lines
        """
        if not box_content:
            return []
        
        seen_content = set()
        deduplicated = []
        
        for line_idx, full_line, content in box_content:
            # Normalize content for comparison (strip, lowercase)
            content_normalized = content.strip().lower()
            
            # Skip if we've seen this exact content before
            if content_normalized and content_normalized in seen_content:
                continue
            
            if content_normalized:
                seen_content.add(content_normalized)
            deduplicated.append(full_line)
        
        return deduplicated

    def _fix_arrow_alignment(self, lines: List[str]) -> List[str]:
        """
        Fix arrow alignment - ensure arrows are aligned with connection points (┬, ├, ┤, ┴).
        Common issue: arrows appear at start of line instead of aligned with connection points.
        ONLY modifies lines containing arrows - preserves all other line positions.
        
        Args:
            lines: List of lines
            
        Returns:
            List of lines with arrows properly aligned
        """
        if not lines:
            return lines
        
        arrow_chars = ["↓", "→", "↑", "←"]
        connection_chars = ["┬", "├", "┤", "┴", "┼"]
        
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check if this line has arrows
            has_arrow = any(char in line for char in arrow_chars)
            
            if has_arrow and i > 0:
                # Check previous line for connection points
                prev_line = lines[i - 1]
                has_connection = any(char in prev_line for char in connection_chars)
                
                if has_connection:
                    # Find all connection point positions in previous line
                    connection_positions = []
                    for j, char in enumerate(prev_line):
                        if char in connection_chars:
                            connection_positions.append(j)
                    
                    if connection_positions:
                        # Find all arrow positions in current line
                        arrow_data = []  # (position, arrow_char)
                        for j, char in enumerate(line):
                            if char in arrow_chars:
                                arrow_data.append((j, char))
                        
                        if arrow_data:
                            # Check if this is an arrow-only line (no other meaningful content)
                            line_without_arrows = line
                            for arrow_pos, arrow_char in arrow_data:
                                # Replace arrows with spaces for checking
                                if arrow_pos < len(line_without_arrows):
                                    line_without_arrows = line_without_arrows[:arrow_pos] + " " + line_without_arrows[arrow_pos+1:]
                            
                            is_arrow_only = not line_without_arrows.strip()
                            
                            if is_arrow_only:
                                # For arrow-only lines, rebuild from scratch with proper spacing
                                max_conn_pos = max(connection_positions)
                                fixed_line_chars = [" "] * (max_conn_pos + 1)
                                
                                # Place each arrow at its nearest connection point
                                for arrow_pos, arrow_char in arrow_data:
                                    nearest_conn = min(connection_positions, key=lambda x: abs(x - arrow_pos))
                                    fixed_line_chars[nearest_conn] = arrow_char
                                
                                fixed_line_str = "".join(fixed_line_chars).rstrip()
                            else:
                                # Line has other content - preserve structure, just move arrows
                                fixed_line = list(line)
                                
                                # Remove all arrows from their current positions
                                for arrow_pos, _ in arrow_data:
                                    if arrow_pos < len(fixed_line):
                                        fixed_line[arrow_pos] = " "
                                
                                # Align each arrow with the nearest connection point
                                for arrow_pos, arrow_char in arrow_data:
                                    nearest_conn = min(connection_positions, key=lambda x: abs(x - arrow_pos))
                                    
                                    # Ensure we have enough space
                                    while len(fixed_line) <= nearest_conn:
                                        fixed_line.append(" ")
                                    
                                    # Place arrow at connection point
                                    fixed_line[nearest_conn] = arrow_char
                                
                                fixed_line_str = "".join(fixed_line).rstrip()
                            
                            fixed_lines.append(fixed_line_str)
                            continue
            
            # No arrow or no connection point - keep line as-is
            fixed_lines.append(line)
        
        return fixed_lines

    def validate_and_clean(self, content: str, strict: bool = False, minimal_clean: bool = False) -> Tuple[str, ValidationResult]:
        """
        Validate and clean content in one operation.

        Args:
            content: ASCII content
            strict: Whether to use strict validation
            minimal_clean: If True, only do minimal cleaning (remove markdown, trailing spaces)

        Returns:
            Tuple of (cleaned_content, validation_result)
        """
        # First clean (minimal for art mode if requested)
        if minimal_clean and self.mode == "art":
            cleaned = self.clean_minimal(content)
        else:
            cleaned = self.clean(content)

        # Then validate the cleaned version
        result = self.validate(cleaned, strict=strict)

        return cleaned, result

    def clean_chunk_fast(self, chunk: str) -> str:
        """
        Fast, lightweight cleaning for streaming chunks.
        Only does essential character filtering - no alignment or complex operations.
        OPTIMIZED: Uses join + list comprehension for maximum speed.

        Args:
            chunk: Small chunk of text from stream

        Returns:
            Cleaned chunk
        """
        # Ultra-fast character filtering using list comprehension
        # Set lookup is O(1), this is blazingly fast
        return ''.join(c for c in chunk if c in self.allowed_chars or c == '\n')


def measure_art_quality(content: str) -> dict:
    """
    Measure ASCII art quality based on ascii-art.de principles.
    Returns a score (0-100) and detailed metrics.

    Args:
        content: ASCII art content

    Returns:
        Dict with 'score' (0-100), 'grade' (A-F), and 'metrics' breakdown
    """
    if not content or not content.strip():
        return {'score': 0, 'grade': 'F', 'metrics': {}}

    lines = [l for l in content.split('\n') if l.strip()]
    if not lines:
        return {'score': 0, 'grade': 'F', 'metrics': {}}

    # Metrics
    line_count = len(lines)
    all_content = ''.join(lines)
    total_chars = len(all_content)
    spaces = all_content.count(' ')
    fill_ratio = (total_chars - spaces) / total_chars if total_chars > 0 else 0

    # Feature characters (eyes, curves, structural)
    feature_chars = set('oO@.^(){}[]<>vV/\\|_-=~')
    unique_features = len(set(c for c in all_content if c in feature_chars))

    # Consecutive repetition
    normalized = [''.join(l.split()) for l in lines]
    max_consecutive = 1
    consecutive = 1
    for i in range(1, len(normalized)):
        if normalized[i] == normalized[i-1] and normalized[i]:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 1

    # Line length variety
    lengths = [len(l.strip()) for l in lines]
    length_variety = len(set(lengths)) / len(lengths) if lengths else 0

    # Scoring (each metric contributes to total)
    scores = {}

    # Line count score (4-12 ideal: 100, 13-15: 70, 16-20: 40, >20: 0)
    if 4 <= line_count <= 12:
        scores['line_count'] = 100
    elif line_count <= 15:
        scores['line_count'] = 70
    elif line_count <= 20:
        scores['line_count'] = 40
    else:
        scores['line_count'] = 0

    # Density score (40-60% ideal: 100, 61-70%: 60, >70%: 20)
    if 0.40 <= fill_ratio <= 0.60:
        scores['density'] = 100
    elif fill_ratio < 0.40:
        scores['density'] = 70  # Too sparse but acceptable
    elif fill_ratio <= 0.70:
        scores['density'] = 60
    else:
        scores['density'] = 20

    # Feature variety score (3+ features: 100, 2: 70, 1: 40, 0: 0)
    if unique_features >= 3:
        scores['features'] = 100
    elif unique_features >= 2:
        scores['features'] = 70
    elif unique_features >= 1:
        scores['features'] = 40
    else:
        scores['features'] = 0

    # Repetition score (1-3 consecutive: 100, 4: 60, 5+: 0)
    if max_consecutive <= 3:
        scores['repetition'] = 100
    elif max_consecutive == 4:
        scores['repetition'] = 60
    else:
        scores['repetition'] = 0

    # Variety score (based on line length diversity)
    scores['variety'] = int(length_variety * 100)

    # Calculate weighted total
    weights = {'line_count': 0.25, 'density': 0.25, 'features': 0.2,
               'repetition': 0.2, 'variety': 0.1}
    total_score = sum(scores[k] * weights[k] for k in weights)

    # Grade
    if total_score >= 90:
        grade = 'A'
    elif total_score >= 80:
        grade = 'B'
    elif total_score >= 70:
        grade = 'C'
    elif total_score >= 60:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'score': int(total_score),
        'grade': grade,
        'metrics': {
            'line_count': line_count,
            'fill_ratio': round(fill_ratio * 100, 1),
            'unique_features': unique_features,
            'max_consecutive_repeat': max_consecutive,
            'length_variety': round(length_variety * 100, 1),
            'scores': scores
        }
    }


class StreamingValidator:
    """
    High-performance validator for real-time streaming content.
    Validates and cleans chunks as they arrive with minimal latency.
    Detects and stops repetitive patterns in real-time.
    """

    def __init__(self, mode: str = "art"):
        """
        Initialize streaming validator.

        Args:
            mode: Validation mode - "art", "chart", or "diagram"
        """
        self.mode = mode.lower()
        self.validator = ASCIIValidator(mode=mode)
        self.accumulated = ""
        self.buffer = ""
        self.last_lines = []  # Track last few lines for repetition detection
        self.repeat_count = 0
        self.stopped = False  # Flag to stop streaming if repetition detected

    def process_chunk(self, chunk: str) -> str:
        """
        Process a streaming chunk with real-time validation.
        Extremely fast - filters characters and detects repetition.

        Args:
            chunk: Incoming text chunk

        Returns:
            Validated chunk ready for display, or empty string if stopped
        """
        # If we've already stopped due to repetition, don't process more
        if self.stopped:
            return ""

        # Fast character filtering - this is blazing fast
        cleaned_chunk = self.validator.clean_chunk_fast(chunk)

        # Strip markdown code block markers in real-time
        # Check if this chunk contains ``` (markdown code block)
        if '```' in cleaned_chunk:
            # Remove lines that are just markdown markers
            lines = cleaned_chunk.split('\n')
            filtered_lines = []
            for line in lines:
                stripped = line.strip()
                # Skip lines that are markdown code blocks or language identifiers
                if stripped == '```' or stripped.startswith('```'):
                    continue
                filtered_lines.append(line)
            cleaned_chunk = '\n'.join(filtered_lines)

        self.accumulated += cleaned_chunk

        # Check for repetitive patterns in real-time
        # For charts, be more lenient - don't stop on legitimate chart patterns
        if self._detect_repetition():
            # Only stop if we have substantial content (prevent stopping too early)
            if len(self.accumulated.strip()) > 50:  # At least 50 chars before stopping
                self.stopped = True
                return ""  # Stop yielding content
            # Otherwise, continue - might be legitimate chart structure

        return cleaned_chunk

    def _detect_repetition(self) -> bool:
        """
        Detect if we're getting repetitive content in real-time.
        VERY LENIENT: Only stops on extreme repetition (12+ identical lines).
        Legitimate ASCII art can have repeated patterns, so we're conservative.
        For charts: More lenient to allow legitimate chart patterns.

        Returns:
            True if excessive repetition detected, False otherwise
        """
        # Split accumulated content into lines
        lines = self.accumulated.split("\n")

        # For charts, be more lenient - charts can have repetitive patterns legitimately
        if self.mode == "chart":
            # Need at least 15 lines to detect repetition in charts
            if len(lines) < 15:
                return False

            recent_lines = [line.strip() for line in lines[-15:] if line.strip()]
            if len(recent_lines) < 12:
                return False

            # Normalize lines (remove all spacing)
            normalized = [''.join(line.split()) for line in recent_lines[-12:]]

            # Only stop on EXTREME repetition for charts (12+ identical lines)
            if normalized and len(set(normalized)) == 1 and normalized[0]:
                return True
            return False

        # For art/diagrams: VERY LENIENT - only stop on extreme cases
        # Need at least 12 lines to detect repetition
        if len(lines) < 12:
            return False

        # Check the last several lines
        recent_lines = [line.strip() for line in lines[-15:] if line.strip()]

        if len(recent_lines) < 12:
            return False

        # Normalize lines (remove all spacing)
        normalized = [''.join(line.split()) for line in recent_lines[-12:]]

        # Check for simple patterns (very short, few unique chars)
        if normalized:
            first_pattern = normalized[0]
            unique_chars = len(set(first_pattern))
            pattern_length = len(first_pattern)

            is_simple = pattern_length <= 3 and unique_chars <= 2

            if is_simple:
                # Simple patterns: stop after 8 identical lines (was 4)
                if len(set(normalized[:8])) == 1 and normalized[0]:
                    return True
            else:
                # Complex patterns: stop after 12 identical lines (was 6)
                if len(set(normalized)) == 1 and normalized[0]:
                    return True

        return False

    def finalize(self) -> str:
        """
        Finalize accumulated content with full validation and cleaning.
        Called after streaming is complete.

        Returns:
            Fully cleaned and validated content
        """
        # If we stopped due to repetition, the accumulated content already has the repetition
        # The clean() method will further process it

        # Do the heavy lifting: alignment, trailing space removal, repetition removal, etc.
        cleaned, _ = self.validator.validate_and_clean(self.accumulated, strict=False)
        return cleaned
