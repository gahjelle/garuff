"""Inline directives suppress a rule line by line — observed end-to-end via the CLI.

A `# garuff: ignore[CODE]` directive silences exactly the named codes on exactly
its own physical line. These cases drive `main()` over a throwaway project and
assert on what a user sees: which violations survive, which directive errors are
reported, and the exit code. See ADR-0001, ADR-0011, CONTEXT.md (**Directive**).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun

# Two over-limit functions: GAC008 fires on each `def` line (1 and 5).
TWO_WIDE_FUNCTIONS = (
    "def wide(a, b):\n"
    "    return a + b\n"
    "\n"
    "\n"
    "def also_wide(a, b):\n"
    "    return a + b\n"
)


def test_directive_silences_its_code_on_its_own_line_only(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A directive on the first `def` line silences GAC008 there, not on line 5."""
    project(
        {
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):", "def wide(a, b):  # garuff: ignore[GAC008]"
            )
        }
    )

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == []
    assert run.at("mod.py", line=5, col=1) == ["GAC008"]
    assert run.exit_code == 1


def test_directive_naming_an_unknown_code_is_reported(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`ignore[GAC999]` names no rule, so it is reported at the marker's column."""
    project({"mod.py": "x = 1  # garuff: ignore[GAC999]\n"})

    run = lint(["mod.py"])

    assert [error.message for error in run.directive_errors] == [
        "unknown code GAC999"
    ]
    assert (run.directive_errors[0].line, run.directive_errors[0].col) == (1, 10)
    assert run.codes == []
    assert run.exit_code == 1
