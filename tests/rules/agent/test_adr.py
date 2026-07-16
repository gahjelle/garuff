"""Shared ADR project-scope behaviour: recognition, scope, and GAA interaction.

Tests that span both GAA rules or exercise the shared `adr.py` seam
(which files count as ADRs, when the check runs at all) live here; each rule's
own unique behaviour lives in `test_adr_duplicate.py` / `test_adr_consecutive.py`.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


def test_adr_directory_out_of_scope_is_silent_no_op(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A broken docs/adr/ that isn't named in scope produces no GAA violations."""
    project(
        {
            "src/mod.py": "x = 1\n",
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 0
    assert not any(code.startswith("GAA") for code in run.codes)


def test_clean_adr_directory_yields_no_violations(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A gapless, duplicate-free docs/adr/ named in scope passes cleanly."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0002-b.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 0


def test_non_adr_files_in_the_directory_are_ignored(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """README.md, a template, and a non-4-digit-prefixed file are not ADRs."""
    project(
        {
            "docs/adr/README.md": "# ADRs\n",
            "docs/adr/template.md": "# Template\n",
            "docs/adr/1-x.md": "# Not four digits\n",
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0002-b.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 0, run.stdout
    assert not any(code.startswith("GAA") for code in run.codes)


def test_duplicate_without_gap_does_not_also_flag_gaa002(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A duplicated number with an otherwise gapless set of numbers is GAA001 only."""
    project(
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
            "docs/adr/0002-c.md": "# ADR\n",
        }
    )

    run = lint(["docs/adr"])

    assert run.exit_code == 1
    assert "GAA001" in run.codes
    assert "GAA002" not in run.codes
