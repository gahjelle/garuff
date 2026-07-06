"""runner.run consumes a resolved Config — per-file-ignores select rules per file.

The runner does no ignore parsing of its own (that is `config.load`'s job); it
receives a resolved `Config` and, per file, drops the source/text rules whose
codes a matching `per-file-ignores` glob silences. These tests build a real
config with `config.load`, then drive `run` at that seam.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff.config import load
from garuff.rules import REGISTRY
from garuff.runner import run

if TYPE_CHECKING:
    from garuff.schemas import RunResult

FUTURE_IMPORT = "from __future__ import annotations\n"


def codes_at(result: RunResult, relpath: str, root: Path) -> list[str]:
    """Return the violation codes reported for the file at `relpath` under root."""
    target = root / relpath
    return [v.rule.code for v in result.violations if v.location.path == target]


def test_per_file_ignore_silences_matching_files_only(tmp_path: Path) -> None:
    """A `tests/**` glob silences GAC001 under tests/ but not under src/."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "mod.py").write_text(FUTURE_IMPORT, encoding="utf-8")
    (tmp_path / "tests" / "test_mod.py").write_text(FUTURE_IMPORT, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n'
        '[tool.garuff.per-file-ignores]\n"tests/**" = ["GAC001"]\n',
        encoding="utf-8",
    )
    config = load(root=tmp_path, registry=REGISTRY)

    result = run(paths=[tmp_path / "src", tmp_path / "tests"], config=config)

    assert codes_at(result, "src/mod.py", tmp_path) == ["GAC001"]
    assert codes_at(result, "tests/test_mod.py", tmp_path) == []
