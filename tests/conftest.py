"""Shared fixtures: the throwaway fixture project every rule test lints.

garuff runs *inside a target project* — it walks up to the nearest
`pyproject.toml`, then lints from there. So a test lays down a disposable
project on disk under `tmp_path` and points garuff at it. The `project` fixture
is that builder behind one seam, so no test re-implements it.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import main
from tests.lintrun import LintRun

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_PYPROJECT = '[project]\nname = "sample"\n'


@pytest.fixture
def project(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[dict[str, str]], Path]:
    """Build a throwaway project under `tmp_path` and chdir into it.

    `files` maps a project-relative path to its text content; parent
    directories are created as needed. A `pyproject.toml` is written from a
    default `[project]` stub unless `files` supplies its own. Returns the
    project root.
    """

    def build(files: dict[str, str]) -> Path:
        """Write `pyproject.toml` and `files`, then chdir to the root."""
        if "pyproject.toml" not in files:
            (tmp_path / "pyproject.toml").write_text(
                DEFAULT_PYPROJECT, encoding="utf-8"
            )
        for relpath, content in files.items():
            path = tmp_path / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        return tmp_path

    return build


@pytest.fixture
def lint(capsys: pytest.CaptureFixture[str]) -> Callable[[list[str]], LintRun]:
    """Run garuff over `paths` in the current project and parse the outcome.

    Pairs with the `project` fixture: build a project, then lint it. Returns a
    `LintRun` carrying the exit code, raw stdout/stderr, and parsed violations.
    """

    def run(paths: list[str]) -> LintRun:
        """Invoke main() over `paths` and capture the run as a LintRun."""
        exit_code = main(paths)
        captured = capsys.readouterr()
        return LintRun(exit_code=exit_code, stdout=captured.out, stderr=captured.err)

    return run
