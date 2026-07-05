"""The stdout parser behind the `lint` fixture: round-trip and unit coverage.

The round-trip test drives a real violation through `main()` so the parser is
pinned to `output.py`'s actual format; the unit tests cover shapes a single
real violation won't produce (project scope, `: ` inside a message, empty run).
"""

from typing import TYPE_CHECKING

from tests.lintrun import parse

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun


def test_round_trip_parses_real_output(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A real GAC011 violation parses into matching fields and raw stdout line."""
    project({"src/mod.py": "my_thing = 1\n"})

    run = lint(["src"])

    assert run.exit_code == 1
    assert run.stdout == "src/mod.py:1:1: GAC011 no possessive `my` prefix\n"
    (violation,) = run.violations
    assert violation.path == "src/mod.py"
    assert violation.line == 1
    assert violation.col == 1
    assert violation.code == "GAC011"
    assert violation.message == "no possessive `my` prefix"


def test_parses_project_scope_line_without_line_or_col() -> None:
    """A `path/: CODE text` line parses with None line/col and a slash-free path."""
    (violation,) = parse("docs/adr/: GAA001 duplicate ADR number 0001: a.md, b.md\n")

    assert violation.path == "docs/adr"
    assert violation.line is None
    assert violation.col is None
    assert violation.code == "GAA001"
    assert violation.message == "duplicate ADR number 0001: a.md, b.md"


def test_message_may_contain_a_colon_space() -> None:
    """Only the first `: ` splits the locator; a colon in the message survives."""
    (violation,) = parse("a.py:2:5: GAC004 use single backticks: `x`, not ``x``\n")

    assert violation.path == "a.py"
    assert violation.line == 2
    assert violation.col == 5
    assert violation.message == "use single backticks: `x`, not ``x``"


def test_empty_stdout_yields_no_violations() -> None:
    """A clean run (no output) parses to an empty list."""
    assert parse("") == []
