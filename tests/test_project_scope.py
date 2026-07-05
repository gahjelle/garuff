"""End-to-end project-scope behaviour: GAA001/GAA002 driven through main()."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import main

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def make_project(root: Path, files: dict[str, str]) -> None:
    """Lay down a fixture project: a pyproject.toml plus the given files."""
    (root / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n', encoding="utf-8"
    )
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_adr_directory_out_of_scope_is_silent_no_op(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """A broken docs/adr/ that isn't named in scope produces no GAA violations."""
    make_project(
        tmp_path,
        {
            "src/mod.py": "x = 1\n",
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["src"])

    captured = capsys.readouterr()
    assert code == 0
    assert "GAA" not in captured.out


def test_duplicate_adr_number_flags_gaa001(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """A duplicate ADR number in scope is flagged as GAA001 at the directory."""
    make_project(
        tmp_path,
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert "docs/adr/: GAA001 duplicate ADR number 0001: 0001-a.md, 0001-b.md" in out


def test_gap_in_adr_numbers_flags_gaa002(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """A gap in ADR numbering in scope is flagged as GAA002 at the directory."""
    make_project(
        tmp_path,
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert (
        "docs/adr/: GAA002 ADR numbers must be a gapless run from 0001; "
        "got 0001, 0003, expected 0001\N{EN DASH}0002" in out
    )


def test_clean_adr_directory_yields_no_violations(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """A gapless, duplicate-free docs/adr/ named in scope passes cleanly."""
    make_project(
        tmp_path,
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0002-b.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    assert code == 0


def test_missing_0001_flags_gaa002(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Numbering that skips 0001 entirely is flagged as GAA002."""
    make_project(
        tmp_path,
        {
            "docs/adr/0002-b.md": "# ADR\n",
            "docs/adr/0003-c.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert (
        "docs/adr/: GAA002 ADR numbers must be a gapless run from 0001; "
        "got 0002, 0003, expected 0001\N{EN DASH}0002" in out
    )


def test_duplicate_without_gap_does_not_also_flag_gaa002(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """A duplicated number with an otherwise gapless set of numbers is GAA001 only."""
    make_project(
        tmp_path,
        {
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0001-b.md": "# ADR\n",
            "docs/adr/0002-c.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    out = capsys.readouterr().out
    assert code == 1
    assert "GAA001" in out
    assert "GAA002" not in out


def test_non_adr_files_in_the_directory_are_ignored(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """README.md, a template, and a non-4-digit-prefixed file are not ADRs."""
    make_project(
        tmp_path,
        {
            "docs/adr/README.md": "# ADRs\n",
            "docs/adr/template.md": "# Template\n",
            "docs/adr/1-x.md": "# Not four digits\n",
            "docs/adr/0001-a.md": "# ADR\n",
            "docs/adr/0002-b.md": "# ADR\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    code = main(["docs/adr"])

    captured = capsys.readouterr()
    assert code == 0, captured.out
    assert "GAA" not in captured.out
