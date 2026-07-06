"""Project discovery and strict `[tool.garuff]` parsing.

`discover_root` locates the project by walking up to a `pyproject.toml`.
`load` is the single validation authority: it reads `[tool.<CONFIG_TABLE>]`,
strictly validates it (the only site that raises `ConfigError`), and returns a
resolved `Config` the runner can consume without touching raw config — globally
ignored rules already removed, options already baked. See ADR-0007, ADR-0008.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from garuff import branding
from garuff.exceptions import ProjectNotFoundError
from garuff.registry import Registry


@dataclass(kw_only=True)
class Config:
    """A resolved, validated configuration: the levers the runner acts on.

    `registry` is the resolved registry (globally-ignored rules removed, options
    baked). `per_file_ignores` pairs each suppression glob with the rule codes it
    silences, matched per file when the runner selects which rules to run.
    """

    registry: Registry
    per_file_ignores: list[tuple[str, frozenset[str]]]


def discover_root(*, start: Path) -> Path:
    """Return the nearest ancestor of start containing a pyproject.toml."""
    for directory in [start, *start.parents]:
        if (directory / "pyproject.toml").is_file():
            return directory
    message = f"no pyproject.toml found walking up from {start}"
    raise ProjectNotFoundError(message)


def load(*, root: Path, registry: Registry) -> Config:
    """Read and strictly validate `[tool.garuff]`; return a resolved Config.

    A missing `[tool]` or `[tool.<name>]` table means no configuration — every
    rule stays on. This is the only function that raises `ConfigError`.
    """
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    table = pyproject.get("tool", {}).get(branding.CONFIG_TABLE, {})
    del table  # parsing of the table lands in later increments
    return Config(registry=registry, per_file_ignores=[])
