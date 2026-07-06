"""GAC001 no `from __future__ import annotations`: the source-scope check."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest


def test_flags_future_annotations_import(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A source file importing __future__ annotations is flagged as GAC001."""
    project({"src/mod.py": "from __future__ import annotations\n"})

    code = main(["src"])

    out = capsys.readouterr().out
    assert "src/mod.py:1:1: GAC001" in out
    assert code == 1
