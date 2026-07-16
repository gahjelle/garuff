"""GAC004 docstring-backticks: docstrings use single backticks, never double.

garuff docstrings are plain prose where a single backtick marks code; a double
pair is stray reStructuredText. The rule walks every docstring-bearing node
(module, class, function). A single-backtick docstring, or a non-docstring
string literal, is left alone. These cases run end-to-end through a `.py` file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


FLAGGED = {
    "module-docstring": '"""Module ``x`` doc."""\n',
    "class-docstring": 'class C:\n    """Class ``x`` doc."""\n',
    "function-docstring": 'def f():\n    """Doc ``x``."""\n',
}

IGNORED = {
    "single-backtick-docstring": '"""Return `x`."""\n',
    "non-docstring-literal": 'x = "``y``"\n',
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_docstrings(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A docstring containing double backticks is flagged GAC004."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC004" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_docstrings(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A single-backtick docstring or a plain string literal is left alone."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC004" not in run.codes


def test_locates_at_the_docstring(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the docstring node itself (exercises docstring_node)."""
    project({"src/mod.py": 'class C:\n    """Class ``x`` doc."""\n'})

    run = lint(["src"])

    assert run.at("src/mod.py", line=2, col=5) == ["GAC004"]
