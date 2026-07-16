"""Inline directives suppress a rule line by line — observed end-to-end via the CLI.

A `# garuff: ignore[CODE]` directive silences exactly the named codes on exactly
its own physical line. These cases drive `main()` over a throwaway project and
assert on what a user sees: which violations survive, which directive errors are
reported, and the exit code. See ADR-0001, ADR-0011, CONTEXT.md (**Directive**).
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import branding

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun

# Two over-limit functions: GAC008 fires on each `def` line (1 and 5). Both carry
# a docstring so only GAC008 — not GAC010 — bites at those lines.
TWO_WIDE_FUNCTIONS = (
    'def wide(a, b):\n    """Wide."""\n\n\ndef also_wide(a, b):\n    """Also wide."""\n'
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

    assert [error.message for error in run.directive_errors] == ["unknown code GAC999"]
    assert (run.directive_errors[0].line, run.directive_errors[0].col) == (1, 10)
    assert run.codes == []
    assert run.exit_code == 1


@pytest.mark.parametrize(
    "directive",
    [
        "# garuff: ignore",
        "# garuff: ignore foo",
        "# garuff: ignore[GAC008",
        "# garuff: ignore[]",
        "# garuff: ignore[ ]",
        "# garuff: ignore[GAC008,]",
    ],
)
def test_malformed_directive_is_reported(
    *,
    directive: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A marker without a well-formed code list is reported, not silently accepted."""
    project({"mod.py": f"x = 1  {directive}\n"})

    run = lint(["mod.py"])

    assert [error.message for error in run.directive_errors] == [
        "malformed (expected ignore[CODE, ...])"
    ]
    assert (run.directive_errors[0].line, run.directive_errors[0].col) == (1, 10)
    assert run.exit_code == 1


def test_malformed_marker_does_not_void_a_well_formed_sibling(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """One bad marker is reported; the good marker beside it still suppresses."""
    project(
        {
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):",
                "def wide(a, b):  # garuff: ignore[GAC008] garuff: ignore",
            )
        }
    )

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == []
    assert [error.message for error in run.directive_errors] == [
        "malformed (expected ignore[CODE, ...])"
    ]


def test_a_bracket_applies_its_known_codes_and_reports_each_unknown_one(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`ignore[GAC008, GAC998, GAC999]` suppresses GAC008 and reports both unknowns."""
    project(
        {
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):",
                "def wide(a, b):  # garuff: ignore[GAC008, GAC998, GAC999]",
            )
        }
    )

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == []
    assert [error.message for error in run.directive_errors] == [
        "unknown code GAC998",
        "unknown code GAC999",
    ]


@pytest.mark.parametrize(
    "comment",
    [
        "# garuff: ignore[GAC008]",
        "# noqa # garuff: ignore[GAC008]",
        "# garuff: ignore[GAC008]  # noqa",
        "# noqa, garuff: ignore[GAC008]",
        "# garuff: ignore[GAC008]  the reason it is fine here",
        "# garuff:ignore[GAC008]",
    ],
)
def test_marker_is_honoured_anywhere_in_the_comment(
    *,
    comment: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The marker shares its line with other pragmas and a trailing reason."""
    project(
        {
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):", f"def wide(a, b):  {comment}"
            )
        }
    )

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == []
    assert run.directive_errors == []


def test_marker_inside_a_string_literal_does_not_suppress(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Only COMMENT tokens carry directives — a marker in a string is inert text."""
    project(
        {
            "mod.py": (
                'def wide(a, b):\n    """D."""\n    return "# garuff: ignore[GAC008]"\n'
            )
        }
    )

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == ["GAC008"]
    assert run.directive_errors == []


def test_directive_suppresses_a_python_text_scope_violation(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """GAC011 is text-scope, but on a `.py` file its line still carries directives."""
    source = (
        "my_name = 1  # garuff: ignore[GAC011]\n"  # garuff: ignore[GAC011]
        "my_other = 2\n"  # garuff: ignore[GAC011]
    )
    project({"mod.py": source})

    run = lint(["mod.py"])

    assert run.at("mod.py", line=1, col=1) == []
    assert run.at("mod.py", line=2, col=1) == ["GAC011"]


def test_markdown_is_never_scanned_for_directives(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `.md` file gets no token pass, so directive-looking text does not suppress."""
    notes = "my_name  <!-- garuff: ignore[GAC011] -->\n"  # garuff: ignore[GAC011]
    project({"notes.md": notes})

    run = lint(["notes.md"])

    assert run.at("notes.md", line=1, col=1) == ["GAC011"]
    assert run.directive_errors == []
    assert run.exit_code == 1


def test_project_scope_violation_is_never_suppressed_by_a_directive(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """GAA rules run outside the per-file loop, so a directive cannot reach them."""
    project(
        {
            "docs/adr/0001-first.md": "# First\n",
            "docs/adr/0001-second.md": "# Second\n",
            "mod.py": "x = 1  # garuff: ignore[GAA001]\n",
        }
    )

    run = lint(["."])

    assert "GAA001" in run.codes
    assert run.directive_errors == []
    assert run.exit_code == 1


def test_globally_ignored_code_in_a_directive_is_a_silent_no_op(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A real code that global `ignore` turned off is known, so it is not reported."""
    project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            f"[{branding.CONFIG_TABLE}]\n"
            'ignore = ["GAC008"]\n',
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):", "def wide(a, b):  # garuff: ignore[GAC008]"
            ),
        }
    )

    run = lint(["mod.py"])

    assert run.codes == []
    assert run.directive_errors == []
    assert run.exit_code == 0


def test_findings_are_interleaved_by_location_and_counted_separately(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A directive error on line 1 precedes a violation on line 5; both are counted."""
    project(
        {
            "mod.py": TWO_WIDE_FUNCTIONS.replace(
                "def wide(a, b):", "def wide(a, b):  # garuff: ignore[GAC008, GAC999]"
            )
        }
    )

    run = lint(["mod.py"])

    finding_lines = [
        line for line in run.stdout.splitlines() if line and not line.startswith(" ")
    ]
    assert finding_lines == [
        "mod.py:1:20: invalid garuff directive: unknown code GAC999",
        "mod.py:5:1: GAC008 `also_wide` takes 2 positional parameters (at most 1)",
    ]
    assert run.codes_explained == ["GAC008"]
    assert "1 violation, 1 directive error" in run.stderr
    assert run.exit_code == 1
