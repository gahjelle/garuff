"""The explanation appendix, end-to-end through `garuff check` (ADR-0012).

`garuff check` prints one explanation block per *distinct rule that fired*,
after the locator lines, on stdout. These tests drive real projects so the
wiring — dedupe, code-sort, the option-baked header, and the column-0 layout
invariant — is exercised the way a user sees it, not just at the render seam.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from tests.test_config import pyproject

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


def finding_lines(stdout: str) -> list[str]:
    """Return the column-0 lines of stdout — every one is a finding (ADR-0012)."""
    return [line for line in stdout.splitlines() if line and not line.startswith(" ")]


def test_three_distinct_rules_each_get_one_code_sorted_block(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Three rules firing yield all locators plus exactly three sorted blocks."""
    project(
        {
            "src/future.py": "from __future__ import annotations\n",  # GAC001
            "src/wide.py": 'def f(a, b):\n    """Doc."""\n    return a\n',  # GAC008
            "docs/adr/0002-gap.md": "# A decision with no 0001\n",  # GAA002
        }
    )

    run = lint(["src", "docs"])

    assert len(finding_lines(run.stdout)) == 3
    assert run.codes_explained == ["GAA002", "GAC001", "GAC008"]


def test_many_hits_of_one_rule_yield_a_single_block(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Forty violations of one rule produce forty locators and one block."""
    project(
        {f"src/mod{n}.py": "from __future__ import annotations\n" for n in range(40)}
    )

    run = lint(["src"])

    assert len(run.violations) == 40
    assert run.codes_explained == ["GAC001"]


def test_clean_run_writes_nothing_to_stdout(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """No violations means no locators and no appendix — stdout is empty."""
    project({"src/mod.py": "x = 1\n"})

    run = lint(["src"])

    assert run.stdout == ""


def test_only_a_directive_error_has_no_appendix(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A run whose only finding is a directive error gets no appendix (ADR-0011)."""
    project({"src/mod.py": "x = 1  # garuff: ignore[GAC999]\n"})

    run = lint(["src"])

    assert run.directive_errors != []
    assert run.violations == []
    assert run.appendix == ""


def test_every_column_zero_line_is_a_finding(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The layout invariant: exactly the findings occupy column 0 (ADR-0012)."""
    project(
        {
            "src/future.py": "from __future__ import annotations\n",
            "src/wide.py": "def f(a, b):\n    return a\n",
        }
    )

    run = lint(["src"])

    assert len(finding_lines(run.stdout)) == len(run.violations)


def test_configured_option_shows_in_the_appendix_header(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """GAC008's block names the configured ceiling, agreeing with the locators."""
    project(
        {
            "pyproject.toml": pyproject(
                "[tool.garuff.rules.GAC008]\nmax-positional-args = 3\n"
            ),
            "src/four.py": 'def g(a, b, c, d):\n    """Doc."""\n    return a\n',
        }
    )

    run = lint(["src"])

    assert run.codes_explained == ["GAC008"]
    assert "keep positional parameters to at most 3" in run.appendix
    assert "at most 3" in run.stdout
