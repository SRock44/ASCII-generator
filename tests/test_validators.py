"""Validator tests: alignment, validation rules, cleaning, and edge cases.

Quality tests use real example art from examples/ to enforce strict standards.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validators import ASCIIValidator, ValidationResult, StreamingValidator, measure_art_quality

EXAMPLES_DIR = project_root / "examples"


def _load_example(category: str, subject: str) -> dict:
    """Load an example JSON file and return the parsed dict."""
    path = EXAMPLES_DIR / category / f"{subject}.json"
    with open(path) as f:
        return json.load(f)


def _all_example_arts(category: str, subject: str) -> list:
    """Return list of art strings from an example file."""
    data = _load_example(category, subject)
    return [ex["art"] for ex in data["examples"]]


# ──────────────────────────────────────────────────────────────────
# ValidationResult basics
# ──────────────────────────────────────────────────────────────────

def test_validation_result_bool_true():
    r = ValidationResult(True)
    assert bool(r) is True

def test_validation_result_bool_false():
    r = ValidationResult(False, errors=["bad"])
    assert bool(r) is False

def test_validation_result_defaults():
    r = ValidationResult(True)
    assert r.errors == []
    assert r.warnings == []


# ──────────────────────────────────────────────────────────────────
# Indentation / alignment preservation (existing + new)
# ──────────────────────────────────────────────────────────────────

def test_art_minimal_clean_preserves_leading_spaces():
    v = ASCIIValidator(mode="art")
    raw = "   /\\_/\\\n  ( o.o )\n   > ^ <\n"
    cleaned, result = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    assert result.is_valid
    assert cleaned.split("\n")[0].startswith("   "), "Leading indentation must be preserved for art"


def test_art_full_clean_preserves_leading_spaces():
    v = ASCIIValidator(mode="art")
    raw = "    __\n   (oo)\n    ||\n"
    cleaned, result = v.validate_and_clean(raw, strict=False, minimal_clean=False)
    assert cleaned.split("\n")[0].startswith("    "), "Full clean must not strip leading spaces"


def test_conservative_repetition_clean_does_not_truncate_following_content():
    v = ASCIIValidator(mode="art")
    repeated = ("|\n" * 20).rstrip("\n")
    raw = f"{repeated}\nAFTER\nEND\n"
    cleaned = v.clean(raw)
    assert "AFTER" in cleaned and "END" in cleaned, "Cleaner must not truncate content after repetition"


def test_art_outlier_padding_aligns_single_flush_left_line():
    v = ASCIIValidator(mode="art")
    raw = "/\\  /\\\n      ( o.o )\n      > ^ <\n      tail\n"
    cleaned, _ = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    first = cleaned.split("\n")[0]
    assert first.startswith("      "), "Under-indented outlier line should be padded to dominant indentation"


def test_degenerate_template_detected_as_invalid():
    v = ASCIIValidator(mode="art")
    raw = "\n".join(["   /   /|   |\\   \\"] * 12) + "\n"
    _, res = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    assert not res.is_valid
    assert any("degenerate" in e.lower() or "template" in e.lower() for e in res.errors)


# ──────────────────────────────────────────────────────────────────
# Drawing alignment tests
# ──────────────────────────────────────────────────────────────────

def test_well_aligned_art_passes_validation():
    """Uniformly indented art should produce no alignment warnings."""
    v = ASCIIValidator(mode="art")
    art = (
        "    /\\_/\\\n"
        "   ( o.o )\n"
        "   > ^ <\n"
    )
    result = v.validate(art)
    assert result.is_valid

def test_alignment_warning_on_mixed_indentation():
    """Lines with wildly different indentation should trigger a warning."""
    v = ASCIIValidator(mode="art")
    art = (
        "         head\n"
        "body\n"
        "         tail\n"
    )
    result = v.validate(art)
    assert any("alignment" in w.lower() or "indentation" in w.lower() for w in result.warnings), \
        "Mixed indentation should produce an alignment warning"

def test_alignment_warning_strict_mode_fails():
    """In strict mode, alignment warnings should cause validation failure."""
    v = ASCIIValidator(mode="art")
    art = (
        "         head\n"
        "body\n"
        "         tail\n"
    )
    result = v.validate(art, strict=True)
    assert not result.is_valid, "Strict mode should fail on alignment warnings"

def test_zero_indent_art_no_alignment_warning():
    """Art with all lines flush-left should not get alignment warnings."""
    v = ASCIIValidator(mode="art")
    art = "/\\_/\\\n( o.o )\n> ^ <\n"
    result = v.validate(art)
    alignment_warns = [w for w in result.warnings if "alignment" in w.lower() or "indentation" in w.lower()]
    assert len(alignment_warns) == 0

def test_consistent_indent_no_warning():
    """All non-empty lines at same indent should produce no alignment warning."""
    v = ASCIIValidator(mode="art")
    art = "  line1\n  line2\n  line3\n"
    result = v.validate(art)
    alignment_warns = [w for w in result.warnings if "alignment" in w.lower()]
    assert len(alignment_warns) == 0

def test_pad_underindented_outliers_does_not_remove_spaces():
    """Outlier padding must only ADD spaces, never remove them."""
    v = ASCIIValidator(mode="art")
    lines = [
        "      line1",
        "      line2",
        "      line3",
        "      line4",
        "line5",   # outlier
        "      line6",
        "      line7",
    ]
    fixed = v._pad_underindented_outliers(lines)
    # The outlier (line5) should be padded to 6 spaces
    assert fixed[4].startswith("      "), "Outlier should be padded to dominant indent"
    # All other lines should be unchanged
    for i in [0, 1, 2, 3, 5, 6]:
        assert fixed[i] == lines[i], f"Non-outlier line {i} should be unchanged"

def test_pad_underindented_skips_when_no_dominant_indent():
    """When dominant indent is 0, no padding should be applied."""
    v = ASCIIValidator(mode="art")
    lines = ["line1", "line2", "line3", "line4", "  indented"]
    fixed = v._pad_underindented_outliers(lines)
    assert fixed == lines, "No padding when dominant indent is 0"

def test_pad_underindented_skips_when_too_many_outliers():
    """When >25% of lines are outliers, treat as intentional structure."""
    v = ASCIIValidator(mode="art")
    lines = [
        "      a",
        "b",
        "c",
        "      d",
        "      e",
    ]
    fixed = v._pad_underindented_outliers(lines)
    # 2 out of 5 = 40% outliers, should not pad
    assert fixed == lines

def test_clean_normalizes_chart_alignment():
    """Chart mode clean should normalize inconsistent indentation."""
    v = ASCIIValidator(mode="chart")
    raw = "    ┌──────┐\n  │ data │\n      └──────┘\n"
    cleaned = v.clean(raw)
    non_empty = [l for l in cleaned.split("\n") if l.strip()]
    leads = [len(l) - len(l.lstrip()) for l in non_empty]
    assert len(set(leads)) == 1, "Chart clean should normalize all lines to same indentation"


# ──────────────────────────────────────────────────────────────────
# Empty / whitespace-only content
# ──────────────────────────────────────────────────────────────────

def test_empty_content_invalid():
    v = ASCIIValidator(mode="art")
    result = v.validate("")
    assert not result.is_valid
    assert any("empty" in e.lower() for e in result.errors)

def test_whitespace_only_invalid():
    v = ASCIIValidator(mode="art")
    result = v.validate("   \n   \n")
    assert not result.is_valid


# ──────────────────────────────────────────────────────────────────
# Character whitelist enforcement
# ──────────────────────────────────────────────────────────────────

def test_valid_ascii_chars_pass():
    v = ASCIIValidator(mode="art")
    art = "/\\_/\\\n( o.o )\n > ^ <\n"
    result = v.validate(art)
    char_errors = [e for e in result.errors if "disallowed" in e.lower()]
    assert len(char_errors) == 0

def test_unicode_emoji_rejected_in_art_mode():
    v = ASCIIValidator(mode="art")
    art = "/\\_/\\\n( \U0001f600 )\n > ^ <\n"
    result = v.validate(art)
    assert any("disallowed" in e.lower() for e in result.errors)

def test_box_drawing_allowed_in_diagram_mode():
    v = ASCIIValidator(mode="diagram")
    content = "┌───┐\n│ A │\n└───┘\n"
    result = v.validate(content)
    char_errors = [e for e in result.errors if "disallowed" in e.lower()]
    assert len(char_errors) == 0

def test_box_drawing_rejected_in_art_mode():
    v = ASCIIValidator(mode="art")
    content = "┌───┐\n│ A │\n└───┘\n"
    result = v.validate(content)
    assert any("disallowed" in e.lower() for e in result.errors)

def test_block_chars_allowed_in_logo_mode():
    v = ASCIIValidator(mode="logo")
    content = "███\n░░░\n▒▒▒\n"
    result = v.validate(content)
    char_errors = [e for e in result.errors if "disallowed" in e.lower()]
    assert len(char_errors) == 0

def test_arrow_chars_allowed_in_diagram_mode():
    v = ASCIIValidator(mode="diagram")
    content = "┌───┐\n│ A │\n└─┬─┘\n  ↓\n┌─┴─┐\n│ B │\n└───┘\n"
    result = v.validate(content)
    char_errors = [e for e in result.errors if "disallowed" in e.lower()]
    assert len(char_errors) == 0


# ──────────────────────────────────────────────────────────────────
# Line count limits
# ──────────────────────────────────────────────────────────────────

def test_art_mode_max_lines():
    v = ASCIIValidator(mode="art")
    assert v.max_lines == 20

def test_art_exceeds_max_lines():
    v = ASCIIValidator(mode="art")
    art = "\n".join([f"line{i}" for i in range(25)])
    result = v.validate(art)
    assert any("exceeds" in e.lower() and "lines" in e.lower() for e in result.errors)

def test_diagram_allows_more_lines():
    v = ASCIIValidator(mode="diagram")
    assert v.max_lines == 50

def test_logo_allows_most_lines():
    v = ASCIIValidator(mode="logo")
    assert v.max_lines == 100


# ──────────────────────────────────────────────────────────────────
# Line width limits
# ──────────────────────────────────────────────────────────────────

def test_art_max_width():
    v = ASCIIValidator(mode="art")
    assert v.max_width == 80

def test_line_too_wide_detected():
    v = ASCIIValidator(mode="art")
    art = "x" * 90 + "\nshort\n"
    result = v.validate(art)
    assert any("width" in e.lower() or "wide" in e.lower() for e in result.errors)

def test_logo_wider_limit():
    v = ASCIIValidator(mode="logo")
    assert v.max_width == 150


# ──────────────────────────────────────────────────────────────────
# Markdown artifact detection
# ──────────────────────────────────────────────────────────────────

def test_markdown_code_fence_detected():
    v = ASCIIValidator(mode="art")
    art = "```\n/\\_/\\\n( o.o )\n```\n"
    result = v.validate(art)
    assert any("markdown" in e.lower() for e in result.errors)

def test_clean_removes_markdown_fences():
    v = ASCIIValidator(mode="art")
    raw = "```ascii\n/\\_/\\\n( o.o )\n```\n"
    cleaned = v.clean(raw)
    assert "```" not in cleaned

def test_clean_minimal_removes_markdown_fences():
    v = ASCIIValidator(mode="art")
    raw = "```\n/\\_/\\\n( o.o )\n```\n"
    cleaned = v.clean_minimal(raw)
    assert "```" not in cleaned


# ──────────────────────────────────────────────────────────────────
# Trailing whitespace
# ──────────────────────────────────────────────────────────────────

def test_trailing_whitespace_warning():
    v = ASCIIValidator(mode="art")
    art = "/\\_/\\   \n( o.o )\n"
    result = v.validate(art)
    assert any("trailing" in w.lower() for w in result.warnings)

def test_clean_strips_trailing_whitespace():
    v = ASCIIValidator(mode="art")
    raw = "/\\_/\\   \n( o.o )  \n"
    cleaned = v.clean(raw)
    for line in cleaned.split("\n"):
        assert line == line.rstrip(), f"Line should have no trailing whitespace: {line!r}"


# ──────────────────────────────────────────────────────────────────
# Repetition detection
# ──────────────────────────────────────────────────────────────────

def test_extreme_consecutive_repetition_error():
    """11+ consecutive identical lines should error in art mode."""
    v = ASCIIValidator(mode="art")
    art = "header\n" + "| |\n" * 12 + "footer\n"
    result = v.validate(art)
    assert any("repetition" in e.lower() for e in result.errors)

def test_moderate_repetition_allowed():
    """A few repeated lines should not error (legitimate patterns)."""
    v = ASCIIValidator(mode="art")
    art = "  /\\\n" + "  ||\n" * 4 + "  \\/\n"
    result = v.validate(art)
    repetition_errors = [e for e in result.errors if "repetition" in e.lower()]
    assert len(repetition_errors) == 0

def test_extreme_pattern_repetition_error():
    """Same pattern appearing 15+ times should error."""
    v = ASCIIValidator(mode="art")
    art = "\n".join(["xoxoxo"] * 16)
    result = v.validate(art)
    assert any("repetition" in e.lower() or "pattern" in e.lower() for e in result.errors)

def test_conservative_repetition_clean_keeps_moderate():
    """Conservative cleaner should keep up to 15 identical lines."""
    v = ASCIIValidator(mode="art")
    lines = ["| |"] * 10
    result = v._remove_repetitive_patterns_conservative(lines)
    assert len(result) == 10, "10 identical lines should be kept by conservative cleaner"

def test_conservative_repetition_clean_trims_extreme():
    """Conservative cleaner should trim beyond 15 identical lines."""
    v = ASCIIValidator(mode="art")
    lines = ["| |"] * 20
    result = v._remove_repetitive_patterns_conservative(lines)
    assert len(result) == 15, "Should trim to 15 identical lines"


# ──────────────────────────────────────────────────────────────────
# Density check
# ──────────────────────────────────────────────────────────────────

def test_extremely_dense_art_error():
    """Art with >90% fill should be flagged as likely broken."""
    v = ASCIIValidator(mode="art")
    # 100% fill, many lines
    art = "\n".join(["XXXXXXXXXXXXXXXX"] * 10)
    result = v.validate(art)
    assert any("dense" in e.lower() or "broken" in e.lower() for e in result.errors)

def test_normal_density_ok():
    """Art with reasonable density should pass."""
    v = ASCIIValidator(mode="art")
    art = "  /\\  \n /  \\ \n/    \\\n------\n"
    result = v.validate(art)
    density_errors = [e for e in result.errors if "dense" in e.lower()]
    assert len(density_errors) == 0


# ──────────────────────────────────────────────────────────────────
# Incomplete art detection
# ──────────────────────────────────────────────────────────────────

def test_incomplete_art_lone_opening_bracket():
    """Art ending with a lone opening bracket should be flagged as truncated."""
    v = ASCIIValidator(mode="art")
    art = " /\\_/\\\n( o.o )\n(\n"
    result = v.validate(art)
    assert any("incomplete" in e.lower() or "cut off" in e.lower() for e in result.errors)

def test_incomplete_art_lone_opening_brace():
    """Art ending with a lone opening brace should be flagged."""
    v = ASCIIValidator(mode="art")
    art = " /\\_/\\\n( o.o )\n{\n"
    result = v.validate(art)
    assert any("incomplete" in e.lower() or "cut off" in e.lower() for e in result.errors)

def test_complete_art_passes():
    """Well-formed art should not be flagged as incomplete."""
    v = ASCIIValidator(mode="art")
    art = " /\\_/\\\n( o.o )\n > ^ <\n"
    result = v.validate(art)
    incomplete_errors = [e for e in result.errors if "incomplete" in e.lower()]
    assert len(incomplete_errors) == 0

def test_short_last_line_not_flagged():
    """Short decorative/signature last lines should NOT be flagged as incomplete.
    Real art often ends with artist signatures (jgs, fL) or decorative elements.
    """
    v = ASCIIValidator(mode="art")
    # Art ending with a short decorative line (like a tail or paw)
    art = "  /\\_____________/\\\n ( o.o           )\n >.\n"
    result = v.validate(art)
    incomplete_errors = [e for e in result.errors if "incomplete" in e.lower()]
    assert len(incomplete_errors) == 0, "Short decorative endings should not be flagged"

def test_art_ending_with_signature_not_flagged():
    """Art ending with an artist signature should not be flagged."""
    v = ASCIIValidator(mode="art")
    art = "    /\\_/\\\n   ( o.o )\n    > ^ <\n   /|   |\\\njgs\n"
    result = v.validate(art)
    incomplete_errors = [e for e in result.errors if "incomplete" in e.lower()]
    assert len(incomplete_errors) == 0


# ──────────────────────────────────────────────────────────────────
# Diagram-specific: box structure validation
# ──────────────────────────────────────────────────────────────────

def test_diagram_complete_box_valid():
    v = ASCIIValidator(mode="diagram")
    content = "┌───────┐\n│ Hello │\n└───────┘\n"
    result = v.validate(content)
    box_errors = [e for e in result.errors if "incomplete box" in e.lower() or "corner" in e.lower()]
    assert len(box_errors) == 0

def test_diagram_missing_bottom_corners_error():
    v = ASCIIValidator(mode="diagram")
    content = "┌───────┐\n│ Hello │\n│ World │\n"
    result = v.validate(content)
    assert any("incomplete" in e.lower() or "corner" in e.lower() for e in result.errors)

def test_diagram_unmatched_corners_error():
    """Two top-left corners but only one bottom-left should error."""
    v = ASCIIValidator(mode="diagram")
    content = (
        "┌───┐  ┌───┐\n"
        "│ A │  │ B │\n"
        "└───┘  │   │\n"
    )
    result = v.validate(content)
    assert any("corner" in e.lower() or "incomplete" in e.lower() for e in result.errors)

def test_diagram_arrow_inside_box_warning():
    """Arrows between pipes should warn."""
    v = ASCIIValidator(mode="diagram")
    content = "┌──────┐\n│ → A  │\n└──────┘\n"
    result = v.validate(content)
    assert any("arrow" in w.lower() for w in result.warnings)

def test_diagram_complete_boxes_adds_missing_bottom():
    """_complete_incomplete_boxes should add bottom border."""
    v = ASCIIValidator(mode="diagram")
    lines = ["┌───┐", "│ A │"]
    completed = v._complete_incomplete_boxes(lines)
    assert any("└" in l and "┘" in l for l in completed), "Missing bottom border should be added"

def test_diagram_duplicate_box_content_warning():
    """Duplicate content in a box should warn."""
    v = ASCIIValidator(mode="diagram")
    content = "┌───────┐\n│ item  │\n│ item  │\n└───────┘\n"
    result = v.validate(content)
    assert any("duplicate" in w.lower() for w in result.warnings)


# ──────────────────────────────────────────────────────────────────
# Diagram-specific: box cleaning
# ──────────────────────────────────────────────────────────────────

def test_normalize_box_widths_pads_content_lines():
    v = ASCIIValidator(mode="diagram")
    lines = ["┌──────────┐", "│ short│", "└──────────┘"]
    normalized = v._normalize_box_widths(lines)
    widths = [len(l) for l in normalized]
    assert len(set(widths)) == 1, "All lines in a box should have the same width after normalization"

def test_deduplicate_box_lines():
    v = ASCIIValidator(mode="diagram")
    box_content = [
        (1, "│ item  │", "item"),
        (2, "│ item  │", "item"),
        (3, "│ other │", "other"),
    ]
    deduped = v._deduplicate_box_lines(box_content)
    assert len(deduped) == 2, "Duplicate box content lines should be removed"


# ──────────────────────────────────────────────────────────────────
# Arrow alignment fixing
# ──────────────────────────────────────────────────────────────────

def test_fix_arrow_alignment_moves_arrow_to_connection():
    v = ASCIIValidator(mode="diagram")
    lines = [
        "     ┬     ",
        "↓          ",
    ]
    fixed = v._fix_arrow_alignment(lines)
    # Arrow should move to column 5 (where ┬ is)
    arrow_pos = fixed[1].index("↓")
    assert arrow_pos == 5, f"Arrow should be at column 5 (┬ position), got {arrow_pos}"

def test_fix_arrow_alignment_preserves_non_arrow_lines():
    v = ASCIIValidator(mode="diagram")
    lines = [
        "┌───┐",
        "│ A │",
        "└───┘",
    ]
    fixed = v._fix_arrow_alignment(lines)
    assert fixed == lines, "Lines without arrows should be unchanged"


# ──────────────────────────────────────────────────────────────────
# Explanatory text detection
# ──────────────────────────────────────────────────────────────────

def test_explanatory_text_warning():
    v = ASCIIValidator(mode="art")
    art = (
        "/\\_/\\\n"
        "( o.o )\n"
        "This is a very long explanation about how the cat was drawn and why it looks the way it does.\n"
        "Another sentence that explains the design choices and artistic direction of the ASCII art piece.\n"
        "Yet another line of prose that has nothing to do with the actual art and is just an explanation.\n"
    )
    result = v.validate(art)
    assert any("explanatory" in w.lower() for w in result.warnings)


# ──────────────────────────────────────────────────────────────────
# Strict mode
# ──────────────────────────────────────────────────────────────────

def test_strict_mode_fails_on_warnings():
    v = ASCIIValidator(mode="art")
    art = "         head\nbody\n         tail\n"
    result_normal = v.validate(art, strict=False)
    result_strict = v.validate(art, strict=True)
    assert result_normal.is_valid, "Non-strict should pass with only warnings"
    assert not result_strict.is_valid, "Strict should fail when warnings exist"


# ──────────────────────────────────────────────────────────────────
# Mode initialization
# ──────────────────────────────────────────────────────────────────

def test_mode_case_insensitive():
    v = ASCIIValidator(mode="ART")
    assert v.mode == "art"

def test_unknown_mode_defaults_to_art():
    v = ASCIIValidator(mode="unknown")
    assert v.allowed_chars == ASCIIValidator.ASCII_ART_CHARS
    assert v.max_lines == 20
    assert v.max_width == 80


# ──────────────────────────────────────────────────────────────────
# clean_chunk_fast (streaming)
# ──────────────────────────────────────────────────────────────────

def test_clean_chunk_fast_strips_invalid():
    v = ASCIIValidator(mode="art")
    chunk = "hello\U0001f600world\n"
    cleaned = v.clean_chunk_fast(chunk)
    assert "\U0001f600" not in cleaned
    assert "hello" in cleaned and "world" in cleaned

def test_clean_chunk_fast_preserves_newlines():
    v = ASCIIValidator(mode="art")
    chunk = "a\nb\nc\n"
    cleaned = v.clean_chunk_fast(chunk)
    assert cleaned == chunk


# ──────────────────────────────────────────────────────────────────
# StreamingValidator
# ──────────────────────────────────────────────────────────────────

def test_streaming_validator_processes_chunks():
    sv = StreamingValidator(mode="art")
    result = sv.process_chunk("hello\n")
    assert "hello" in result

def test_streaming_validator_stops_on_extreme_repetition():
    sv = StreamingValidator(mode="art")
    # Feed 15 identical lines to trigger repetition detection
    for _ in range(15):
        sv.process_chunk("| |\n")
    result = sv.process_chunk("| |\n")
    assert result == "", "Should stop yielding after extreme repetition"
    assert sv.stopped is True

def test_streaming_validator_finalize():
    sv = StreamingValidator(mode="art")
    sv.process_chunk("/\\_/\\\n")
    sv.process_chunk("( o.o )\n")
    final = sv.finalize()
    assert "/\\_/\\" in final
    assert "( o.o )" in final

def test_streaming_validator_chart_mode_more_lenient():
    sv = StreamingValidator(mode="chart")
    # Feed 10 identical lines -- should NOT stop for charts (needs 12+)
    for _ in range(10):
        sv.process_chunk("█████\n")
    assert sv.stopped is False, "Chart mode should tolerate more repetition"


# ──────────────────────────────────────────────────────────────────
# Art quality: real examples from examples/ must pass validation
# ──────────────────────────────────────────────────────────────────

def test_all_dragon_examples_pass_after_clean():
    """Every dragon example must pass validation after cleaning (the real pipeline)."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("characters", "dragon")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Dragon example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_elephant_examples_pass_after_clean():
    """Every elephant example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("animals", "elephant")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Elephant example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_cat_examples_pass_after_clean():
    """Every cat example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("animals", "cat")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Cat example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_skull_examples_pass_after_clean():
    """Every skull example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("characters", "skull")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Skull example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_rose_examples_pass_after_clean():
    """Every rose example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("nature", "rose")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Rose example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_house_examples_pass_after_clean():
    """Every house example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("objects", "house")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"House example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_wolf_examples_pass_after_clean():
    """Every wolf example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("animals", "wolf")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Wolf example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_guitar_examples_pass_after_clean():
    """Every guitar example must pass validation after cleaning."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("objects", "guitar")):
        cleaned, result = v.validate_and_clean(art, minimal_clean=True)
        assert result.is_valid, (
            f"Guitar example {i} failed validation: {result.errors}\n---\n{art}"
        )

def test_all_examples_pass_validation_sweep():
    """Sweep ALL example files across every category. None should fail after full clean.
    Uses full clean (not minimal) since that's the production pipeline and it normalizes
    characters like tabs that some examples contain.
    """
    v = ASCIIValidator(mode="art")
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            art = ex["art"]
            cleaned, result = v.validate_and_clean(art, minimal_clean=False)
            if not result.is_valid:
                failures.append(f"{subject}[{i}]: {result.errors}")

    assert not failures, (
        f"{len(failures)} example(s) failed validation:\n" + "\n".join(failures[:10])
    )


# ──────────────────────────────────────────────────────────────────
# Art quality: examples must clean without destroying structure
# ──────────────────────────────────────────────────────────────────

def test_clean_preserves_example_structure_dragon():
    """Cleaning a dragon example must not destroy its structure."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("characters", "dragon")):
        cleaned = v.clean(art)
        original_non_empty = [l for l in art.split("\n") if l.strip()]
        cleaned_non_empty = [l for l in cleaned.split("\n") if l.strip()]
        assert len(cleaned_non_empty) >= len(original_non_empty) * 0.8, (
            f"Dragon example {i}: clean removed too many lines "
            f"({len(original_non_empty)} -> {len(cleaned_non_empty)})"
        )

def test_clean_preserves_example_structure_elephant():
    """Cleaning an elephant example must not destroy its structure."""
    v = ASCIIValidator(mode="art")
    for i, art in enumerate(_all_example_arts("animals", "elephant")):
        cleaned = v.clean(art)
        original_non_empty = [l for l in art.split("\n") if l.strip()]
        cleaned_non_empty = [l for l in cleaned.split("\n") if l.strip()]
        assert len(cleaned_non_empty) >= len(original_non_empty) * 0.8, (
            f"Elephant example {i}: clean removed too many lines "
            f"({len(original_non_empty)} -> {len(cleaned_non_empty)})"
        )

def test_clean_preserves_example_structure_sweep():
    """Sweep ALL examples: cleaning must preserve at least 80% of non-empty lines."""
    v = ASCIIValidator(mode="art")
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            art = ex["art"]
            cleaned = v.clean(art)
            orig_lines = [l for l in art.split("\n") if l.strip()]
            clean_lines = [l for l in cleaned.split("\n") if l.strip()]
            if orig_lines and len(clean_lines) < len(orig_lines) * 0.8:
                failures.append(
                    f"{subject}[{i}]: {len(orig_lines)} -> {len(clean_lines)} lines"
                )

    assert not failures, (
        f"{len(failures)} example(s) lost structure during clean:\n" + "\n".join(failures[:10])
    )


# ──────────────────────────────────────────────────────────────────
# Art quality: examples must score well with measure_art_quality
# ──────────────────────────────────────────────────────────────────

def test_quality_empty_is_zero():
    result = measure_art_quality("")
    assert result["score"] == 0
    assert result["grade"] == "F"

def test_quality_dragon_examples_score_well():
    """Dragon examples (complex multi-line art) should score >= 50."""
    for i, art in enumerate(_all_example_arts("characters", "dragon")):
        result = measure_art_quality(art)
        assert result["score"] >= 50, (
            f"Dragon example {i} scored {result['score']} (grade {result['grade']}), "
            f"expected >= 50. Metrics: {result['metrics']}"
        )

def test_quality_elephant_examples_score_well():
    """Elephant examples should score >= 50."""
    for i, art in enumerate(_all_example_arts("animals", "elephant")):
        result = measure_art_quality(art)
        assert result["score"] >= 50, (
            f"Elephant example {i} scored {result['score']} (grade {result['grade']}), "
            f"expected >= 50. Metrics: {result['metrics']}"
        )

def test_quality_cat_examples_score_well():
    """Cat examples should score >= 50."""
    for i, art in enumerate(_all_example_arts("animals", "cat")):
        result = measure_art_quality(art)
        assert result["score"] >= 50, (
            f"Cat example {i} scored {result['score']} (grade {result['grade']}), "
            f"expected >= 50. Metrics: {result['metrics']}"
        )

def test_quality_skull_examples_score_well():
    """Skull examples should score >= 50."""
    for i, art in enumerate(_all_example_arts("characters", "skull")):
        result = measure_art_quality(art)
        assert result["score"] >= 50, (
            f"Skull example {i} scored {result['score']} (grade {result['grade']}), "
            f"expected >= 50. Metrics: {result['metrics']}"
        )

def test_quality_rose_examples_have_feature_variety():
    """Rose examples should have at least 2 unique feature characters."""
    for i, art in enumerate(_all_example_arts("nature", "rose")):
        result = measure_art_quality(art)
        assert result["metrics"]["unique_features"] >= 2, (
            f"Rose example {i} has only {result['metrics']['unique_features']} "
            f"unique features, expected >= 2"
        )

def test_quality_guitar_examples_have_line_variety():
    """Guitar examples should have varied line lengths (not uniform blocks)."""
    for i, art in enumerate(_all_example_arts("objects", "guitar")):
        result = measure_art_quality(art)
        assert result["metrics"]["length_variety"] >= 30, (
            f"Guitar example {i} has only {result['metrics']['length_variety']}% "
            f"line length variety, expected >= 30%"
        )

def test_quality_no_example_has_extreme_repetition():
    """No example art should have >5 consecutive identical lines.
    Real art can have short runs (chair legs, lamp posts) of 4-5, but 6+ indicates broken output.
    """
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            result = measure_art_quality(ex["art"])
            if result["metrics"]["max_consecutive_repeat"] > 5:
                failures.append(
                    f"{subject}[{i}]: {result['metrics']['max_consecutive_repeat']} "
                    f"consecutive repeats"
                )

    assert not failures, (
        f"{len(failures)} example(s) have extreme repetition:\n" + "\n".join(failures[:10])
    )

def test_quality_all_examples_score_above_minimum():
    """ALL example art should score >= 40 (minimum quality bar)."""
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            result = measure_art_quality(ex["art"])
            if result["score"] < 40:
                failures.append(
                    f"{subject}[{i}]: score={result['score']} grade={result['grade']} "
                    f"metrics={result['metrics']}"
                )

    assert not failures, (
        f"{len(failures)} example(s) scored below 40:\n" + "\n".join(failures[:10])
    )


# ──────────────────────────────────────────────────────────────────
# Art quality: known-bad art must be rejected
# ──────────────────────────────────────────────────────────────────

def test_quality_highly_repetitive_scores_low():
    """12 identical lines should score poorly on repetition."""
    art = "\n".join(["||||||||"] * 12)
    result = measure_art_quality(art)
    assert result["metrics"]["max_consecutive_repeat"] > 5
    assert result["metrics"]["scores"]["repetition"] == 0, \
        "12 consecutive identical lines should score 0 on repetition"

def test_quality_single_char_block_scores_low():
    """A solid block of one character is not real art."""
    art = "\n".join(["XXXXXXXXXX"] * 8)
    result = measure_art_quality(art)
    assert result["score"] < 50, f"Solid block scored {result['score']}, expected < 50"

def test_quality_two_line_art_scores_lower_than_examples():
    """Trivially short art should score lower than real examples."""
    trivial = "/\\\n\\/"
    trivial_result = measure_art_quality(trivial)

    real_art = _all_example_arts("animals", "elephant")[0]
    real_result = measure_art_quality(real_art)

    assert real_result["score"] > trivial_result["score"], (
        f"Real elephant art ({real_result['score']}) should outscore trivial art ({trivial_result['score']})"
    )


# ──────────────────────────────────────────────────────────────────
# Art quality: example density matches recorded metadata
# ──────────────────────────────────────────────────────────────────

def test_example_density_within_expected_range():
    """Example art density (from metadata) should be between 20-80%.
    Real ASCII art has varied density; very sparse (<20%) or very dense (>80%) usually
    indicates broken output. Some detailed art reaches ~79%.
    """
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            density = ex.get("density", 0)
            if not (0.20 <= density <= 0.80):
                failures.append(f"{subject}[{i}]: density={density}")

    assert not failures, (
        f"{len(failures)} example(s) have density outside 20-80%:\n" + "\n".join(failures[:10])
    )

def test_example_lines_within_art_mode_limit():
    """Every example should have line count within art mode max_lines."""
    v = ASCIIValidator(mode="art")
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            line_count = ex.get("lines", 0)
            if line_count > v.max_lines:
                failures.append(f"{subject}[{i}]: {line_count} lines > max {v.max_lines}")

    assert not failures, (
        f"{len(failures)} example(s) exceed max lines:\n" + "\n".join(failures[:10])
    )

def test_example_width_within_art_mode_limit():
    """Every example should have width within art mode max_width."""
    v = ASCIIValidator(mode="art")
    index_path = EXAMPLES_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)

    failures = []
    for subject, rel_path in index["subjects"].items():
        example_path = EXAMPLES_DIR / rel_path
        if not example_path.exists():
            continue
        with open(example_path) as f:
            data = json.load(f)
        for i, ex in enumerate(data.get("examples", [])):
            width = ex.get("width", 0)
            if width > v.max_width:
                failures.append(f"{subject}[{i}]: {width} wide > max {v.max_width}")

    assert not failures, (
        f"{len(failures)} example(s) exceed max width:\n" + "\n".join(failures[:10])
    )


# ──────────────────────────────────────────────────────────────────
# validate_and_clean round-trip
# ──────────────────────────────────────────────────────────────────

def test_validate_and_clean_returns_tuple():
    v = ASCIIValidator(mode="art")
    result = v.validate_and_clean("/\\_/\\\n( o.o )\n")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], ValidationResult)

def test_clean_then_validate_passes():
    """Content that was cleaned should pass validation."""
    v = ASCIIValidator(mode="art")
    raw = "```\n  /\\_/\\   \n ( o.o )  \n  > ^ <\n```\n"
    cleaned, result = v.validate_and_clean(raw)
    assert "```" not in cleaned
    # Re-validate the cleaned output
    result2 = v.validate(cleaned)
    assert result2.is_valid, f"Cleaned content should pass validation, errors: {result2.errors}"


# ──────────────────────────────────────────────────────────────────
# Edge cases: clean()
# ──────────────────────────────────────────────────────────────────

def test_clean_empty_returns_empty():
    v = ASCIIValidator(mode="art")
    assert v.clean("") == ""

def test_clean_none_returns_none():
    v = ASCIIValidator(mode="art")
    assert v.clean(None) is None

def test_clean_removes_leading_trailing_blank_lines():
    v = ASCIIValidator(mode="art")
    raw = "\n\n\n/\\_/\\\n( o.o )\n\n\n"
    cleaned = v.clean(raw)
    lines = cleaned.split("\n")
    assert lines[0].strip() != "", "Leading blank lines should be removed"
    assert lines[-1].strip() != "", "Trailing blank lines should be removed"

def test_clean_normalizes_crlf():
    v = ASCIIValidator(mode="art")
    raw = "/\\_/\\\r\n( o.o )\r\n"
    cleaned = v.clean(raw)
    assert "\r" not in cleaned

def test_clean_truncates_art_to_max_lines():
    v = ASCIIValidator(mode="art")
    raw = "\n".join([f"line{i}" for i in range(30)])
    cleaned = v.clean(raw)
    assert len(cleaned.split("\n")) <= v.max_lines

def test_clean_replaces_invalid_chars_with_space():
    v = ASCIIValidator(mode="art")
    raw = "hel\U0001f600lo\n"
    cleaned = v.clean(raw)
    assert "\U0001f600" not in cleaned
    assert "hel" in cleaned and "lo" in cleaned


