"""Validator regression tests (indentation safety, non-destructive cleaning)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validators import ASCIIValidator


def test_art_minimal_clean_preserves_leading_spaces():
    v = ASCIIValidator(mode="art")
    raw = "   /\\_/\\\n  ( o.o )\n   > ^ <\n"
    cleaned, result = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    assert result.is_valid
    assert cleaned.split("\n")[0].startswith("   "), "Leading indentation must be preserved for art"


def test_art_full_clean_preserves_leading_spaces():
    # Some call-sites use validate_and_clean() without minimal_clean=True (e.g., AI clients).
    # Full clean must still not strip indentation.
    v = ASCIIValidator(mode="art")
    raw = "    __\n   (oo)\n    ||\n"
    cleaned, result = v.validate_and_clean(raw, strict=False, minimal_clean=False)
    assert cleaned.split("\n")[0].startswith("    "), "Full clean must not strip leading spaces"


def test_conservative_repetition_clean_does_not_truncate_following_content():
    v = ASCIIValidator(mode="art")
    # 20 identical lines -> extra repeats should be dropped, but content after should remain.
    repeated = ("|\n" * 20).rstrip("\n")
    raw = f"{repeated}\nAFTER\nEND\n"
    cleaned = v.clean(raw)
    assert "AFTER" in cleaned and "END" in cleaned, "Cleaner must not truncate content after repetition"


def test_art_outlier_padding_aligns_single_flush_left_line():
    v = ASCIIValidator(mode="art")
    # Most lines have dominant indent of 6; a single flush-left line should be padded.
    raw = "/\\  /\\\n      ( o.o )\n      > ^ <\n      tail\n"
    cleaned, _ = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    first = cleaned.split("\n")[0]
    assert first.startswith("      "), "Under-indented outlier line should be padded to dominant indentation"


def test_degenerate_template_detected_as_invalid():
    v = ASCIIValidator(mode="art")
    # Many lines collapse to the same structure when whitespace is removed.
    raw = "\n".join(["   /   /|   |\\   \\"] * 12) + "\n"
    _, res = v.validate_and_clean(raw, strict=False, minimal_clean=True)
    assert not res.is_valid
    assert any("degenerate" in e.lower() or "template" in e.lower() for e in res.errors)


