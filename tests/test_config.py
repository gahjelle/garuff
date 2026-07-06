"""config.load — the single validation authority for `[tool.garuff]`.

These tests drive `config.load` directly (the seam that reads and strictly
validates the config table), laying down a throwaway `pyproject.toml` under
`tmp_path` and pointing `load` at it. The registry passed in is the real
`REGISTRY`, so tests reference live rule codes.
"""

from pathlib import Path

import pytest

from garuff.config import Config, load
from garuff.exceptions import ConfigError
from garuff.rules import REGISTRY


def write_pyproject(root: Path, garuff_table: str) -> None:
    """Write a `pyproject.toml` under root with the given `[tool.garuff]` body."""
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "sample"\n{garuff_table}', encoding="utf-8"
    )


def test_no_config_table_leaves_registry_unchanged(tmp_path: Path) -> None:
    """A project without a `[tool.garuff]` table loads every rule (registry intact)."""
    write_pyproject(tmp_path, "")

    config = load(root=tmp_path, registry=REGISTRY)

    assert isinstance(config, Config)
    assert config.registry == REGISTRY


def test_ignore_removes_the_named_rule(tmp_path: Path) -> None:
    """A code in `ignore` is dropped from the resolved registry, others stay."""
    write_pyproject(tmp_path, '[tool.garuff]\nignore = ["GAC001"]\n')

    config = load(root=tmp_path, registry=REGISTRY)

    assert "GAC001" not in config.registry.by_code
    assert "GAC011" in config.registry.by_code


def test_ignore_removes_a_project_scope_rule(tmp_path: Path) -> None:
    """`ignore` is the only lever for a project-scope rule (GAA), and it works."""
    write_pyproject(tmp_path, '[tool.garuff]\nignore = ["GAA001"]\n')

    config = load(root=tmp_path, registry=REGISTRY)

    assert "GAA001" not in config.registry.by_code


def test_unknown_ignore_code_is_a_config_error(tmp_path: Path) -> None:
    """An `ignore` code no rule provides is a hard config error, not a warning."""
    write_pyproject(tmp_path, '[tool.garuff]\nignore = ["GAC999"]\n')

    with pytest.raises(ConfigError, match="GAC999"):
        load(root=tmp_path, registry=REGISTRY)


def test_unknown_top_level_key_is_a_config_error(tmp_path: Path) -> None:
    """A key outside {ignore, per-file-ignores, rules} is a config error."""
    write_pyproject(tmp_path, "[tool.garuff]\nfoo = 1\n")

    with pytest.raises(ConfigError, match="foo"):
        load(root=tmp_path, registry=REGISTRY)


def test_per_file_ignores_are_parsed(tmp_path: Path) -> None:
    """Each `per-file-ignores` entry becomes a (glob, frozenset[codes]) pair."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("x = 1\n", encoding="utf-8")
    write_pyproject(
        tmp_path,
        '[tool.garuff.per-file-ignores]\n"tests/**" = ["GAC001", "GAC011"]\n',
    )

    config = load(root=tmp_path, registry=REGISTRY)

    assert config.per_file_ignores == [("tests/**", frozenset({"GAC001", "GAC011"}))]


def test_unknown_per_file_ignore_code_is_a_config_error(tmp_path: Path) -> None:
    """An unknown code in a `per-file-ignores` value is a config error."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("x = 1\n", encoding="utf-8")
    write_pyproject(
        tmp_path, '[tool.garuff.per-file-ignores]\n"tests/**" = ["GAC999"]\n'
    )

    with pytest.raises(ConfigError, match="GAC999"):
        load(root=tmp_path, registry=REGISTRY)
