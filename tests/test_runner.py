"""Per-file-ignores select rules per file — observed end-to-end through the CLI.

A `per-file-ignores` glob silences its codes only for the files it matches; a
file outside the glob still trips them. These cases drive `main()` over a
throwaway project and assert on the violations a user sees, file by file.
"""

from typing import TYPE_CHECKING

from garuff import branding

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun

FUTURE_IMPORT = "from __future__ import annotations\n"  # trips GAC001


def test_per_file_ignore_silences_matching_files_only(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `tests/**` glob silences GAC001 under tests/ but not under src/."""
    project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            f"[{branding.CONFIG_TABLE}.per-file-ignores]\n"
            '"tests/**" = ["GAC001"]\n',
            "src/mod.py": FUTURE_IMPORT,
            "tests/test_mod.py": FUTURE_IMPORT,
        }
    )

    run = lint(["src", "tests"])

    assert run.at("src/mod.py", 1, 1) == ["GAC001"]
    assert run.at("tests/test_mod.py", 1, 1) == []
