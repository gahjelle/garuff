"""GAA001 duplicate ADR number: the check for a repeated numeric prefix."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest


def test_duplicate_adr_number_flags_gaa001(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A duplicate ADR number in scope is flagged as GAA001 at the directory."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
        }
    )

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert "docs/adr/: GAA001 duplicate ADR number 0001: 0001-a.md, 0001-b.md" in out
