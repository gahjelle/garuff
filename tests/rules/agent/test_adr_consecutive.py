"""GAA002 consecutive ADR numbers: the check for a gapless run from 0001."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun

GAPLESS_MESSAGE = (
    "ADR numbers must be a gapless run from 0001; "
    "got {got}, expected 0001\N{EN DASH}0002"
)


def test_gap_in_adr_numbers_flags_gaa002(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A gap in ADR numbering in scope is flagged as GAA002 at the directory."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 1
    assert run.at("docs/adr") == ["GAA002"]
    (violation,) = run.violations
    assert violation.message == GAPLESS_MESSAGE.format(got="0001, 0003")


def test_missing_0001_flags_gaa002(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Numbering that skips 0001 entirely is flagged as GAA002."""
    project(
        {
            "docs/adr/0002-b.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 1
    assert run.at("docs/adr") == ["GAA002"]
    (violation,) = run.violations
    assert violation.message == GAPLESS_MESSAGE.format(got="0002, 0003")
