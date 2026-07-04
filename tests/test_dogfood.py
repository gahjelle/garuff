"""Dogfood: garuff must pass its own rules against its own source."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_own_src_is_clean(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running garuff against its own src/ reports no violations."""
    monkeypatch.chdir(PROJECT_ROOT)

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 0, captured.out
