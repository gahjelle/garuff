"""GAC002 base-model: models inherit `FrozenModel`/`StrictModel`, not `BaseModel`.

A class subclassing `BaseModel` directly opts out of the project's strict/frozen
defaults. The two project bases (`FrozenModel`/`StrictModel`) are themselves
exempt. These cases run end-to-end through a `.py` file so registration is
exercised too.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


FLAGGED = {
    "bare-base-model": "class User(BaseModel):\n    x: int\n",
    "dotted-base-model": "class User(pydantic.BaseModel):\n    x: int\n",
}

IGNORED = {
    "frozen-model-base-name": "class FrozenModel(BaseModel):\n    x: int\n",
    "strict-model-base-name": "class StrictModel(BaseModel):\n    x: int\n",
    "inherits-frozen-model": "class User(FrozenModel):\n    x: int\n",
    "inherits-strict-model": "class User(StrictModel):\n    x: int\n",
    "unrelated-base": "class User(object):\n    x: int\n",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_models(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A class subclassing `BaseModel` directly is flagged GAC002."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC002" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_models(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A project base itself, or a class using one, is left alone (no GAC002)."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC002" not in run.codes


def test_locates_at_the_class_line(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the `class` line and column."""
    project({"src/mod.py": "class User(BaseModel):\n    x: int\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", line=1, col=1) == ["GAC002"]
