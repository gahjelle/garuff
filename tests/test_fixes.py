"""Unit tests for the apply layer — turning located Edits into new text.

These test `fixes.apply_edits` and its offset helpers directly, at the seam a
fixer produces (`Edit`) and the runner consumes (the rewritten text plus the
edits actually applied). Overlap-skipping, the `original` guard, and
high-offset-first ordering are the invariants a fixer relies on but cannot see.
"""

from pathlib import Path

from garuff.fixes import apply_edits, line_starts, offset_at
from garuff.schemas import Edit, Location


def edit(*, start: int, end: int, original: str, replacement: str) -> Edit:
    """Build an Edit with a throwaway Location — the apply layer ignores it."""
    return Edit(
        location=Location(path=Path("x.py"), line=1, col=1),
        start=start,
        end=end,
        original=original,
        replacement=replacement,
    )


def test_apply_edits_applies_a_single_edit() -> None:
    """One edit replaces its half-open slice and is reported as applied."""
    text = "hello world"

    new_text, applied = apply_edits(
        text, edits=[edit(start=6, end=11, original="world", replacement="there")]
    )

    assert new_text == "hello there"
    assert len(applied) == 1


def test_two_non_overlapping_edits_both_apply_regardless_of_order() -> None:
    """Both edits land whether given low-first or high-first (spliced high-first)."""
    text = "abcdef"
    low = edit(start=0, end=1, original="a", replacement="AA")
    high = edit(start=4, end=6, original="ef", replacement="E")

    for order in ([low, high], [high, low]):
        new_text, applied = apply_edits(text, edits=order)
        assert new_text == "AAbcdE"
        assert len(applied) == 2


def test_overlapping_edit_is_skipped_and_reported_not_applied() -> None:
    """The second of two overlapping edits is skipped; only the first applies."""
    text = "abcdef"
    first = edit(start=1, end=4, original="bcd", replacement="X")
    second = edit(start=2, end=5, original="cde", replacement="Y")

    new_text, applied = apply_edits(text, edits=[first, second])

    assert new_text == "aXef"
    assert applied == [first]


def test_original_mismatch_skips_edit_and_leaves_text_unchanged() -> None:
    """A guard mismatch (`text[start:end] != original`) drops the edit entirely."""
    text = "hello world"

    new_text, applied = apply_edits(
        text, edits=[edit(start=6, end=11, original="WORLD", replacement="there")]
    )

    assert new_text == "hello world"
    assert applied == []


def test_offset_at_round_trips_against_location_from_offset() -> None:
    """offset_at inverts Location.from_offset across a multi-line text."""
    text = "one\ntwo\nthree\n"
    starts = line_starts(text)

    for offset in range(len(text)):
        location = Location.from_offset(text=text, offset=offset, path=Path("x.py"))
        assert location.line is not None
        assert location.col is not None
        assert offset_at(line=location.line, col=location.col, starts=starts) == offset
