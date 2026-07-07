"""GAC001 no `from __future__ import annotations`: the source-scope check."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun


def test_flags_future_annotations_import(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A source file importing __future__ annotations is flagged as GAC001."""
    project({"src/mod.py": "from __future__ import annotations\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", line=1, col=1) == ["GAC001"]
    assert run.exit_code == 1
