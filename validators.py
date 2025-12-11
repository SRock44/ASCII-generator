"""Validators for ASCII art strictness enforcement."""
from typing import Tuple, List, Optional
import re


class ValidationResult:
    """Result of validation check."""

    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        """
        Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

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
            mode: Validation mode - "art", "chart", or "diagram"
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
        else:  # Default to art mode
            self.allowed_chars = self.ASCII_ART_CHARS
            self.max_lines = 50
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

        # 8. Mode-specific validations
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
                    # Boxes should have matching corners
                    if not (corner_counts["┌"] == corner_counts["└"] and
                            corner_counts["┐"] == corner_counts["┘"]):
                        warnings.append(
                            "Incomplete box structures detected (mismatched corners: "
                            f"top-left: {corner_counts['┌']}, bottom-left: {corner_counts['└']}, "
                            f"top-right: {corner_counts['┐']}, bottom-right: {corner_counts['┘']})"
                        )

        # Determine if valid
        is_valid = len(errors) == 0
        if strict and warnings:
            # In strict mode, warnings also fail validation
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

        # Remove markdown code blocks AGGRESSIVELY
        content = content.strip()

        # Remove ALL lines that contain only ```
        lines = content.split("\n")
        lines = [line for line in lines if line.strip() != "```" and not line.strip().startswith("```")]

        # Remove language identifiers like ```ascii or ```text
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() in ["```", "```\n"]:
            lines = lines[:-1]

        content = "\n".join(lines).strip()
        lines = content.split("\n")

        # Remove trailing whitespace from all lines
        lines = [line.rstrip() for line in lines]

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Remove repetitive pattern lines (like | | repeated 50 times)
        lines = self._remove_repetitive_patterns(lines)

        # Fix alignment to MINIMUM indentation (STRICT - normalize to leftmost position)
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            leading_spaces = [len(line) - len(line.lstrip()) for line in non_empty_lines]

            # Use MINIMUM indentation as base (leftmost position)
            # This preserves the leftmost content and normalizes everything to it
            min_indent = min(leading_spaces)

            # STRICT: Fix ANY variation in leading spaces
            if max(leading_spaces) - min(leading_spaces) > 0:
                fixed_lines = []
                for line in lines:
                    if line.strip():
                        # Normalize to minimum indent (leftmost)
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
        # RELAXED: Only stop on EXTREME repetition (15+ lines)
        # Let the AI be creative! Don't limit legitimate patterns.
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

            # Only detect EXTREME stuck patterns (very simple + many repeats)
            # This catches infinite loops without limiting creativity
            is_extreme_simple = (
                len(line_normalized) <= 2 and  # Extremely short (≤2 chars)
                len(set(line_normalized)) == 1  # Single character repeated
            )

            if is_extreme_simple:
                # Only the most basic patterns get limited
                threshold = 8  # Allow up to 8 even for simplest patterns
            else:
                # Everything else: very generous threshold
                threshold = max_allowed_occurrences

            # Detect repetitive patterns
            if last_line_normalized and line_normalized == last_line_normalized:
                repeat_count += 1
                if repeat_count <= threshold:
                    cleaned.append(line)
                else:
                    # Only stop on truly extreme repetition
                    break
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

    def validate_and_clean(self, content: str, strict: bool = False) -> Tuple[str, ValidationResult]:
        """
        Validate and clean content in one operation.

        Args:
            content: ASCII content
            strict: Whether to use strict validation

        Returns:
            Tuple of (cleaned_content, validation_result)
        """
        # First clean
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
        self.accumulated += cleaned_chunk

        # Check for repetitive patterns in real-time
        if self._detect_repetition():
            self.stopped = True
            return ""  # Stop yielding content

        return cleaned_chunk

    def _detect_repetition(self) -> bool:
        """
        Detect if we're getting repetitive content in real-time.
        RELAXED: Only stops on EXTREME repetition (12+ identical lines).
        Allows creative patterns and legitimate structure.

        Returns:
            True if extreme repetition detected, False otherwise
        """
        # Split accumulated content into lines
        lines = self.accumulated.split("\n")

        # Need at least 12 lines to detect EXTREME repetition
        if len(lines) < 12:
            return False

        # Check the last several lines
        recent_lines = [line.strip() for line in lines[-15:] if line.strip()]

        if len(recent_lines) < 12:
            return False

        # Normalize lines (remove all spacing)
        normalized = [''.join(line.split()) for line in recent_lines[-12:]]

        # Only stop on EXTREME cases: 12+ identical lines
        # This catches infinite loops without limiting creativity
        if len(set(normalized)) == 1 and normalized[0]:
            # Same pattern repeated 12+ times - definitely stuck in loop
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
