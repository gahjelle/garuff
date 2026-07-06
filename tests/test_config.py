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
from garuff.rules.code.positional_args import PositionalArgs


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


def test_dead_glob_matching_no_files_is_a_config_error(tmp_path: Path) -> None:
    """A `per-file-ignores` glob that matches no project file is a config error."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    write_pyproject(
        tmp_path, '[tool.garuff.per-file-ignores]\n"nowhere/**" = ["GAC001"]\n'
    )

    with pytest.raises(ConfigError, match="nowhere/"):
        load(root=tmp_path, registry=REGISTRY)


def test_live_glob_is_judged_against_the_whole_project(tmp_path: Path) -> None:
    """A glob matching files anywhere in the project passes (ADR-0008).

    The universe is the whole project, not any narrower lint path, so a
    `tests/**` glob is live as long as the project has files under `tests/`.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_mod.py").write_text("x = 1\n", encoding="utf-8")
    write_pyproject(
        tmp_path, '[tool.garuff.per-file-ignores]\n"tests/**" = ["GAC001"]\n'
    )

    config = load(root=tmp_path, registry=REGISTRY)

    assert config.per_file_ignores == [("tests/**", frozenset({"GAC001"}))]


def test_unknown_top_level_key_is_a_config_error(tmp_path: Path) -> None:
    """A key outside {ignore, per-file-ignores, rules} is a config error."""
    write_pyproject(tmp_path, "[tool.garuff]\nfoo = 1\n")

    with pytest.raises(ConfigError, match="foo"):
        load(root=tmp_path, registry=REGISTRY)


def test_options_for_an_optionless_rule_is_a_config_error(tmp_path: Path) -> None:
    """A `rules.<CODE>` table for a rule with no options is a config error."""
    write_pyproject(tmp_path, "[tool.garuff.rules.GAC001]\nfoo = 1\n")

    with pytest.raises(ConfigError, match="GAC001"):
        load(root=tmp_path, registry=REGISTRY)


def test_unknown_option_key_is_a_config_error(tmp_path: Path) -> None:
    """An option key the rule's schema does not declare is a config error."""
    write_pyproject(tmp_path, "[tool.garuff.rules.GAC008]\nnonsense = 1\n")

    with pytest.raises(ConfigError, match="nonsense"):
        load(root=tmp_path, registry=REGISTRY)


def test_wrong_option_type_is_a_config_error(tmp_path: Path) -> None:
    """An option value of the wrong type is a config error, not a coercion."""
    write_pyproject(
        tmp_path, '[tool.garuff.rules.GAC008]\nmax-positional-args = "two"\n'
    )

    with pytest.raises(ConfigError, match="max-positional-args"):
        load(root=tmp_path, registry=REGISTRY)


def test_unknown_rule_code_in_options_is_a_config_error(tmp_path: Path) -> None:
    """A `rules.<CODE>` table for an unknown code is a config error."""
    write_pyproject(tmp_path, "[tool.garuff.rules.GAC999]\nmax-positional-args = 2\n")

    with pytest.raises(ConfigError, match="GAC999"):
        load(root=tmp_path, registry=REGISTRY)


def test_option_override_is_baked_into_the_resolved_rule(tmp_path: Path) -> None:
    """A valid override is baked onto the resolved rule via dataclasses.replace."""
    write_pyproject(tmp_path, "[tool.garuff.rules.GAC008]\nmax-positional-args = 3\n")

    config = load(root=tmp_path, registry=REGISTRY)

    rule = config.registry.by_code["GAC008"]
    assert isinstance(rule, PositionalArgs)
    assert rule.options.max_positional_args == 3


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
