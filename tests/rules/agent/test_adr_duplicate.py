"""GAA001 duplicate ADR number: the check for a repeated numeric prefix."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


def test_duplicate_adr_number_flags_gaa001(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A duplicate ADR number in scope is flagged as GAA001 at the directory."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 1
    assert run.at("docs/adr") == ["GAA001"]
    (violation,) = run.violations
    assert violation.message == "duplicate ADR number 0001: 0001-a.md, 0001-b.md"
