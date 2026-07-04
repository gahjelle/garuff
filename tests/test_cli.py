"""End-to-end CLI behaviour: drive main() against tmp_path fixture projects."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    import pytest


def make_project(root: Path, files: dict[str, str]) -> None:
    """Lay down a fixture project: a pyproject.toml plus the given files.

    files maps a project-relative path to its text content.
    """
    (root / "pyproject.toml").write_text('[project]\nname = "sample"\n')
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def test_flags_future_annotations_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A source file importing __future__ annotations is flagged as GAC001."""
    make_project(tmp_path, {"src/mod.py": "from __future__ import annotations\n"})
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    out = capsys.readouterr()
    assert "src/mod.py:1:1: GAC001" in out.out
    assert code == 1


def test_prints_summary_to_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A summary line goes to stderr, leaving stdout for locator lines only."""
    make_project(tmp_path, {"src/mod.py": "from __future__ import annotations\n"})
    monkeypatch.chdir(tmp_path)

    main(["src"])

    captured = capsys.readouterr()
    assert "1 .py-file" in captured.err
    assert "1 violation" in captured.err
    assert "GAC001" not in captured.err  # locator lines stay on stdout
