"""Tests for the passive result and value types in schemas.py."""

from pathlib import Path

from garuff.rule import Rule
from garuff.schemas import Location, Violation


def test_sort_key_orders_by_path_then_line_then_col() -> None:
    """Locations sort by path, then line, then column."""
    locations = [
        Location(path=Path("z.py"), line=1, col=1),
        Location(path=Path("a.py"), line=3, col=1),
        Location(path=Path("a.py"), line=1, col=5),
        Location(path=Path("a.py"), line=1, col=1),
    ]
    assert sorted(locations, key=lambda loc: loc.sort_key) == [
        Location(path=Path("a.py"), line=1, col=1),
        Location(path=Path("a.py"), line=1, col=5),
        Location(path=Path("a.py"), line=3, col=1),
        Location(path=Path("z.py"), line=1, col=1),
    ]


def test_directory_level_location_renders_bare_path_with_trailing_slash() -> None:
    """A `Location` with no line/col renders as `path/`, no `:line:col`."""
    location = Location(path=Path("docs/adr"))

    assert location.render(root=Path()) == "docs/adr/"


def test_directory_level_location_sorts_before_same_path_with_line() -> None:
    """A directory-level location treats missing line/col as 0 for sorting."""
    location = Location(path=Path("docs/adr"))

    assert location.sort_key == ("docs/adr", 0, 0)


def test_violation_detail_overrides_rule_summary_in_render() -> None:
    """A `Violation` with a detail renders that detail, not the rule summary."""
    rule = Rule(
        code="GAA001", summary="duplicate ADR numeric prefix", rationale="", fix=""
    )
    violation = Violation(
        rule=rule,
        location=Location(path=Path("docs/adr")),
        detail="duplicate ADR number 0001: 0001-a.md, 0001-b.md",
    )

    assert violation.render(root=Path()) == (
        "docs/adr/: GAA001 duplicate ADR number 0001: 0001-a.md, 0001-b.md"
    )


def test_violation_without_detail_falls_back_to_rule_summary() -> None:
    """A `Violation` with no detail renders the rule's summary, as before."""
    rule = Rule(
        code="GAC001",
        summary="no `from __future__ import annotations`",
        rationale="",
        fix="",
    )
    violation = Violation(
        rule=rule, location=Location(path=Path("a.py"), line=1, col=1)
    )

    assert violation.render(root=Path()) == (
        "a.py:1:1: GAC001 no `from __future__ import annotations`"
    )
