"""Tests for the passive result and value types in schemas.py."""

from pathlib import Path

from garuff.schemas import Location


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
