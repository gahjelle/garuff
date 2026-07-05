"""GAA002 consecutive ADR numbers: the check for a gapless run from 0001."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    from collections.abc import Callable

    from _pytest.capture import CaptureFixture


def test_gap_in_adr_numbers_flags_gaa002(
    project: Callable[[dict[str, str]], Path],
    capsys: CaptureFixture[str],
) -> None:
    """A gap in ADR numbering in scope is flagged as GAA002 at the directory."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        }
    )

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert (
        "docs/adr/: GAA002 ADR numbers must be a gapless run from 0001; "
        "got 0001, 0003, expected 0001\N{EN DASH}0002" in out
    )


def test_missing_0001_flags_gaa002(
    project: Callable[[dict[str, str]], Path],
    capsys: CaptureFixture[str],
) -> None:
    """Numbering that skips 0001 entirely is flagged as GAA002."""
    project(
        {
            "docs/adr/0002-b.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        }
    )

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert (
        "docs/adr/: GAA002 ADR numbers must be a gapless run from 0001; "
        "got 0002, 0003, expected 0001\N{EN DASH}0002" in out
    )
