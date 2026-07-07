"""End-to-end CLI & runner contract: exit codes, path handling, summary, sort.

Rule-specific behaviour lives under `tests/rules/`; this file asserts what the
CLI and runner do around the rules — how paths are discovered, how counts and
exit codes are reported, and how violations from different scopes are ordered.
Where a violation is needed as a fixture, GAC001 is used as a convenient trip.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import branding, main

if TYPE_CHECKING:
    from collections.abc import Callable


def test_clean_project_exits_zero(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A project with no violations prints no locators and exits 0."""
    project({"src/mod.py": "x = 1\n"})

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
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An explicitly-named path that does not exist is an error (exit 2)."""
    project({"src/mod.py": "x = 1\n"})

    code = main(["does_not_exist"])

    err = capsys.readouterr().err
    assert code == 2
    assert "does_not_exist" in err


def test_default_lints_root_without_a_tests_dir(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Bare `garuff` lints the root even when the project has no tests/ dir.

    The default is the project root (which always exists), so a project with
    only `src/` still lints cleanly — no "does not exist" error for a path
    garuff itself chose.
    """
    project({"src/mod.py": "from __future__ import annotations\n"})

    code = main([])

    captured = capsys.readouterr()
    assert code == 1
    assert "src/mod.py:1:1: GAC001" in captured.out
    assert "does not exist" not in captured.err


def test_defaults_lint_whole_root_including_docs(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no paths given, the whole root is linted, so project (GAA) rules run.

    `docs/adr/` is outside the old `[src, tests]` default; a bare run reporting
    its GAA violation proves the default now widens to the project root and the
    ADR project rules run without being named.
    """
    project(
        {
            "src/a.py": "x = 1\n",
            "tests/test_a.py": "from __future__ import annotations\n",
            "docs/adr/0002-gap.md": "# A decision with no 0001\n",
        }
    )

    code = main([])

    captured = capsys.readouterr()
    assert code == 1
    assert "tests/test_a.py:1:1: GAC001" in captured.out
    assert "GAA002" in captured.out


def test_unparsable_file_is_reported_and_skipped(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A file that can't be parsed is reported, skipped, and exits 1."""
    project(
        {
            "src/good.py": "x = 1\n",
            "src/bad.py": "def broken(\n",
        }
    )

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 1
    assert "src/bad.py" in captured.err
    assert "could not parse" in captured.err
    assert "1 .py file linted" in captured.err
    assert "1 skipped" in captured.err


def test_prints_summary_to_stderr(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A summary line goes to stderr, leaving stdout for locator lines only."""
    project({"src/mod.py": "from __future__ import annotations\n"})

    main(["src"])

    captured = capsys.readouterr()
    assert "1 .py file" in captured.err
    assert "1 violation" in captured.err
    assert "GAC001" not in captured.err  # locator lines stay on stdout


def test_summary_splits_counts_by_extension(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The summary counts each extension separately, .md before .py."""
    project(
        {
            "src/a.py": "x = 1\n",
            "src/b.py": "y = 2\n",
            "docs/guide.md": "All clear here.\n",
        }
    )

    code = main(["src", "docs"])

    captured = capsys.readouterr()
    assert code == 0
    assert "1 .md file, 2 .py files linted: 0 violations" in captured.err


def test_source_and_text_violations_reported_line_sorted(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One file with a source (GAC001) and text (GAC011) hit reports both, line-sorted.

    The text hit is on line 1 (a docstring), the source hit on line 2 (the
    __future__ import) — so a runner that emits source rules before text rules
    would misorder them without the (path, line, col) sort.
    """
    source = '"""my_helper docstring."""\nfrom __future__ import annotations\n'
    project({"src/mod.py": source})

    code = main(["src"])

    lines = capsys.readouterr().out.splitlines()
    assert code == 1
    assert lines == [
        "src/mod.py:1:4: GAC011 no possessive `my` prefix",
        "src/mod.py:2:1: GAC001 no `from __future__ import annotations`",
    ]


def test_invalid_config_exits_two(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken `[tool.garuff]` config aborts before linting, exit 2 with a message."""
    project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            '[tool.garuff]\nignore = ["GAC999"]\n',
            "src/mod.py": "x = 1\n",
        }
    )

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 2
    assert "GAC999" in captured.err
    assert captured.out == ""


def test_non_git_tree_warns_exactly_once_and_still_lints(
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Outside a git work-tree garuff warns once, then lints with Layer 1 only."""
    project(
        {
            "src/mod.py": "from __future__ import annotations\n",
            ".venv/lib/junk.py": "from __future__ import annotations\n",
        }
    )

    code = main(["."])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.count("not a git repository") == 1
    assert "src/mod.py:1:1: GAC001" in captured.out
    assert ".venv" not in captured.out  # Layer 1 still prunes the virtualenv


def test_help_usage_reflects_program_name(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The usage line is branded from branding.PROGRAM_NAME, not a hardcoded literal."""
    monkeypatch.setattr(branding, "PROGRAM_NAME", "rebrandtest")

    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "rebrandtest" in capsys.readouterr().out
