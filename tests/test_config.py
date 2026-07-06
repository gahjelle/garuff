"""config.load — the single validation authority for `[tool.garuff]`.

These tests drive `config.load` directly (the seam that reads and strictly
validates the config table), laying down a throwaway `pyproject.toml` under
`tmp_path` and pointing `load` at it. The registry passed in is the real
`REGISTRY`, so tests reference live rule codes.
"""

from pathlib import Path

from garuff.config import Config, load
from garuff.rules import REGISTRY


def test_no_config_table_leaves_registry_unchanged(tmp_path: Path) -> None:
    """A project without a `[tool.garuff]` table loads every rule (registry intact)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n', encoding="utf-8"
    )

    config = load(root=tmp_path, registry=REGISTRY)

    assert isinstance(config, Config)
    assert config.registry == REGISTRY
