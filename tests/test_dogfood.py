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


def test_own_dogfood_scope_is_clean(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The full `just dogfood` scope (src, tests, docs/adr) reports no violations.

    Linting `tests/` exercises the repo's own `per-file-ignores`: fixture data
    and helpers there trip GAC008/GAC011 by design, so the config silences those
    codes under `tests/**`. A clean run proves both the rules and the ignores.
    """
    monkeypatch.chdir(PROJECT_ROOT)

    code = main(["src", "tests", "docs/adr"])

    captured = capsys.readouterr()
    assert code == 0, captured.out
