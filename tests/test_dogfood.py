"""Dogfood: garuff must pass its own rules against its own source."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_own_src_is_clean(
    *,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running garuff against its own src/ reports no violations."""
    monkeypatch.chdir(PROJECT_ROOT)

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 0, captured.out


def test_own_whole_root_is_clean(
    *,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Bare `garuff` over the whole project root reports no violations.

    This is the default scope (`just dogfood`): src, tests, docs, and the ADRs,
    with `.venv`/dot-dirs/gitignored trees excluded. Linting `tests/` exercises
    the repo's own `per-file-ignores`: fixture data and helpers there trip
    GAC008/GAC011 by design, so the config silences those codes under
    `tests/**`. A clean run proves both the rules and the ignores.
    """
    monkeypatch.chdir(PROJECT_ROOT)

    code = main([])

    captured = capsys.readouterr()
    assert code == 0, captured.out
