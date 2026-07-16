"""GAC009 dataclass-kw-only: `@dataclass(kw_only=True)` so fields stay named.

A positional dataclass ties every call site to field order. Any `@dataclass`
without `kw_only=True` is flagged; a `kw_only=True` dataclass or a non-dataclass
class is left alone. These cases run end-to-end through a `.py` file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


FLAGGED = {
    "bare-decorator": "@dataclass\nclass C:\n    x: int\n",
    "empty-call": "@dataclass()\nclass C:\n    x: int\n",
    "frozen-only": "@dataclass(frozen=True)\nclass C:\n    x: int\n",
    "dotted-decorator": "@dataclasses.dataclass\nclass C:\n    x: int\n",
}

IGNORED = {
    "kw-only-true": "@dataclass(kw_only=True)\nclass C:\n    x: int\n",
    "frozen-and-kw-only": (
        "@dataclass(frozen=True, kw_only=True)\nclass C:\n    x: int\n"
    ),
    "non-dataclass": "class C:\n    x: int\n",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_dataclasses(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `@dataclass` without `kw_only=True` is flagged GAC009."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC009" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_dataclasses(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `kw_only=True` dataclass or a non-dataclass class is left alone."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC009" not in run.codes


def test_locates_at_the_class_line(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the `class` line, not the decorator."""
    project({"src/mod.py": "@dataclass\nclass C:\n    x: int\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", line=2, col=1) == ["GAC009"]
