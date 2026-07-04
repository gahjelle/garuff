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
    (root / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n', encoding="utf-8"
    )
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


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


def test_clean_project_exits_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A project with no violations prints no locators and exits 0."""
    make_project(tmp_path, {"src/mod.py": "x = 1\n"})
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == ""
    assert "0 violations" in captured.err


def test_missing_pyproject_exits_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no pyproject.toml up the tree, garuff errors clearly (exit 2)."""
    work = tmp_path / "loose"
    work.mkdir()
    (work / "mod.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(work)

    code = main(["mod.py"])

    err = capsys.readouterr().err
    assert code == 2
    assert "pyproject.toml" in err


def test_explicit_missing_path_exits_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An explicitly-named path that does not exist is an error (exit 2)."""
    make_project(tmp_path, {"src/mod.py": "x = 1\n"})
    monkeypatch.chdir(tmp_path)

    code = main(["does_not_exist"])

    err = capsys.readouterr().err
    assert code == 2
    assert "does_not_exist" in err


def test_default_missing_tests_dir_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing default path (no tests/) is skipped, not an error."""
    make_project(tmp_path, {"src/mod.py": "from __future__ import annotations\n"})
    monkeypatch.chdir(tmp_path)

    code = main([])

    captured = capsys.readouterr()
    assert code == 1
    assert "src/mod.py:1:1: GAC001" in captured.out
    assert "does not exist" not in captured.err


def test_defaults_lint_both_src_and_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no paths given, both src/ and tests/ are linted."""
    make_project(
        tmp_path,
        {
            "src/a.py": "x = 1\n",
            "tests/test_a.py": "from __future__ import annotations\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main([])

    out = capsys.readouterr().out
    assert code == 1
    assert "tests/test_a.py:1:1: GAC001" in out


def test_unparsable_file_is_reported_and_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A file that can't be parsed is reported, skipped, and exits 1."""
    make_project(
        tmp_path,
        {
            "src/good.py": "x = 1\n",
            "src/bad.py": "def broken(\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 1
    assert "src/bad.py" in captured.err
    assert "could not parse" in captured.err
    assert "1 file linted" in captured.err
    assert "1 skipped" in captured.err


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
    assert "1 file" in captured.err
    assert "1 violation" in captured.err
    assert "GAC001" not in captured.err  # locator lines stay on stdout


def test_flags_possessive_my_in_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A possessive-`my` name in a .py source is flagged as GAC011."""
    make_project(tmp_path, {"src/mod.py": "my_thing = 1\n"})
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    out = capsys.readouterr().out
    assert "src/mod.py:1:1: GAC011" in out
    assert code == 1


def test_flags_possessive_my_in_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A possessive-`my` name in a Markdown file is flagged as GAC011."""
    make_project(tmp_path, {"docs/guide.md": "See the `MyClass` helper.\n"})
    monkeypatch.chdir(tmp_path)

    code = main(["docs/guide.md"])

    out = capsys.readouterr().out
    assert "docs/guide.md:1:10: GAC011" in out
    assert code == 1


def test_source_and_text_violations_reported_line_sorted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One file with a source (GAC001) and text (GAC011) hit reports both, line-sorted.

    The text hit is on line 1 (a docstring), the source hit on line 2 (the
    __future__ import) — so a runner that emits source rules before text rules
    would misorder them without the (path, line, col) sort.
    """
    source = '"""my_helper docstring."""\nfrom __future__ import annotations\n'
    make_project(tmp_path, {"src/mod.py": source})
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    lines = capsys.readouterr().out.splitlines()
    assert code == 1
    assert lines == [
        "src/mod.py:1:4: GAC011 no possessive `my` prefix",
        "src/mod.py:2:1: GAC001 no `from __future__ import annotations`",
    ]
