"""Project discovery and strict `[tool.garuff]` parsing.

`discover_root` locates the project by walking up to a `pyproject.toml`.
`load` is the single validation authority: it reads `[tool.<CONFIG_TABLE>]`,
strictly validates it (the only site that raises `ConfigError`), and returns a
resolved `Config` the runner can consume without touching raw config — globally
ignored rules already removed, options already baked. See ADR-0007, ADR-0008.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from garuff import branding
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.registry import Registry
from garuff.runner import gather_files

# The only keys `[tool.garuff]` may hold; anything else is a config error.
TOP_LEVEL_KEYS = frozenset({"ignore", "per-file-ignores", "rules"})


@dataclass(kw_only=True)
class Config:
    """A resolved, validated configuration: the levers the runner acts on.

    `registry` is the resolved registry (globally-ignored rules removed, options
    baked). `per_file_ignores` pairs each suppression glob with the rule codes it
    silences, matched per file when the runner selects which rules to run. `root`
    is the project root those globs are anchored to (POSIX, root-relative).
    """

    root: Path
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
    for key in table:
        if key not in TOP_LEVEL_KEYS:
            message = f"unknown key in [tool.{branding.CONFIG_TABLE}]: {key}"
            raise ConfigError(message)

    ignore = table.get("ignore", [])
    for code in ignore:
        require_known_code(code, registry=registry)
    resolved = Registry(
        rules=[rule for rule in registry.rules if rule.code not in ignore]
    )

    per_file_ignores: list[tuple[str, frozenset[str]]] = []
    for glob, codes in table.get("per-file-ignores", {}).items():
        for code in codes:
            require_known_code(code, registry=registry)
        require_live_glob(glob, root=root)
        per_file_ignores.append((glob, frozenset(codes)))

    return Config(root=root, registry=resolved, per_file_ignores=per_file_ignores)


def require_known_code(code: str, *, registry: Registry) -> None:
    """Raise `ConfigError` unless the code names a rule in the full registry."""
    if code not in registry.by_code:
        message = f"unknown rule code in configuration: {code}"
        raise ConfigError(message)


def require_live_glob(glob: str, *, root: Path) -> None:
    """Raise `ConfigError` unless the glob matches at least one project file.

    "The project" is the whole tree under root — `gather_files([root])`, not the
    files a given run lints — so partial runs never trip on globs aimed at trees
    they aren't linting (ADR-0008).
    """
    for file in gather_files(paths=[root]):
        relative = PurePosixPath(file.relative_to(root).as_posix())
        if relative.full_match(glob):
            return
    message = f"per-file-ignores glob matches no files: {glob}"
    raise ConfigError(message)
