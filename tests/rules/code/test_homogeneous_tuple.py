"""GAC005 homogeneous-tuple: use `list[T]`, not `tuple[T, ...]`.

A `tuple[T, ...]` is a variable-length tuple — a homogeneous sequence dressed as
a fixed record. A fixed-length `tuple[int, str]` or a plain `list[int]` is left
alone. These cases run end-to-end through a `.py` file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


FLAGGED = {
    "return-annotation": "def f() -> tuple[int, ...]:\n    return ()\n",
    "variable-annotation": "x: tuple[str, ...]\n",
}

IGNORED = {
    "fixed-length-tuple": "x: tuple[int, str]\n",
    "plain-list": "x: list[int]\n",
    "dotted-non-tuple": "x: typing.Deque[int]\n",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_tuples(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `tuple[T, ...]` annotation is flagged GAC005."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC005" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_tuples(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A fixed-length tuple or a non-tuple subscript is left alone (no GAC005)."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC005" not in run.codes


def test_locates_at_the_subscript(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the `tuple[T, ...]` subscript."""
    project({"src/mod.py": "x: tuple[str, ...]\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", line=1, col=4) == ["GAC005"]
