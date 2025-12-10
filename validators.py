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

    def validate(self, content: str, strict: bool = True) -> ValidationResult:
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

        # Remove markdown code blocks
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        lines = content.split("\n")

        # Remove trailing whitespace from all lines
        lines = [line.rstrip() for line in lines]

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Fix alignment to most common indentation (STRICT - always fix any variation)
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            from collections import Counter
            leading_spaces = [len(line) - len(line.lstrip()) for line in non_empty_lines]

            # Use most common indentation as base
            counter = Counter(leading_spaces)
            most_common_indent = counter.most_common(1)[0][0]

            # STRICT: Fix ANY variation in leading spaces (not just >2)
            if max(leading_spaces) - min(leading_spaces) > 0:
                fixed_lines = []
                for line in lines:
                    if line.strip():
                        # Normalize to most common indent
                        fixed_lines.append(" " * most_common_indent + line.lstrip())
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

        # Truncate to max lines
        if len(lines) > self.max_lines:
            lines = lines[:self.max_lines]

        # Truncate lines to max width
        lines = [line[:self.max_width] if len(line) > self.max_width else line
                 for line in lines]

        return "\n".join(lines)

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

    def process_chunk(self, chunk: str) -> str:
        """
        Process a streaming chunk with real-time validation.
        Extremely fast - only filters characters, no complex operations.

        Args:
            chunk: Incoming text chunk

        Returns:
            Validated chunk ready for display
        """
        # Fast character filtering - this is blazing fast
        cleaned_chunk = self.validator.clean_chunk_fast(chunk)
        self.accumulated += cleaned_chunk
        return cleaned_chunk

    def finalize(self) -> str:
        """
        Finalize accumulated content with full validation and cleaning.
        Called after streaming is complete.

        Returns:
            Fully cleaned and validated content
        """
        # Now do the heavy lifting: alignment, trailing space removal, etc.
        cleaned, _ = self.validator.validate_and_clean(self.accumulated, strict=False)
        return cleaned
