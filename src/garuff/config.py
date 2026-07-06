"""Project discovery and strict parsing of the tool's config table.

`discover_root` locates the project by walking up to a `pyproject.toml`.
`load` is the single validation authority: it reads the `branding.CONFIG_TABLE`
table, strictly validates it (the only site that raises `ConfigError`), and
returns a resolved `Config` the runner can consume without touching raw config —
globally ignored rules already removed, options already baked. See ADR-0007,
ADR-0008.
"""

import tomllib
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from garuff import branding
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.files import GitScope, PerFileIgnore, gather_files, relative_posix
from garuff.registry import Registry
from garuff.rule import ProjectRule

if TYPE_CHECKING:
    from garuff.rule import Rule

# The only keys the config table may hold; anything else is a config error.
TOP_LEVEL_KEYS = frozenset({"ignore", "per-file-ignores", "rules"})


@dataclass(kw_only=True)
class Config:
    """A resolved, validated configuration: the levers the runner acts on.

    `registry` is the resolved registry (globally-ignored rules removed, options
    baked). `per_file_ignores` is the suppression entries, each matched per file
    when the runner selects which rules to run. `root` is the project root those
    globs are anchored to (POSIX, root-relative).
    """

    root: Path
    registry: Registry
    per_file_ignores: list[PerFileIgnore]


def discover_root(*, start: Path) -> Path:
    """Return the nearest ancestor of start containing a pyproject.toml."""
    for directory in [start, *start.parents]:
        if (directory / "pyproject.toml").is_file():
            return directory
    message = f"no pyproject.toml found walking up from {start}"
    raise ProjectNotFoundError(message)


def load(*, root: Path, registry: Registry, scope: GitScope) -> Config:
    """Read and strictly validate the tool's config table; return a resolved Config.

    A missing config table means no configuration — every rule stays on. This is
    the only function that raises `ConfigError`. `scope` is git's view of the
    work-tree, threaded into the whole-project glob-liveness walk so it honours
    the same exclusions a run does.
    """
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    table: Any = pyproject
    for key in branding.CONFIG_TABLE_PATH:
        table = table.get(key, {})
    for key in table:
        if key not in TOP_LEVEL_KEYS:
            message = f"unknown key in [{branding.CONFIG_TABLE}]: {key}"
            raise ConfigError(message)

    ignore = table.get("ignore", [])
    for code in ignore:
        require_known_code(code, registry=registry)

    baked_options = resolve_options(table.get("rules", {}), registry=registry)
    resolved = Registry(
        rules=[
            (
                replace(rule, options=baked_options[rule.code])
                if rule.code in baked_options
                else rule
            )
            for rule in registry.rules
            if rule.code not in ignore
        ]
    )

    per_file_ignores: list[PerFileIgnore] = []
    for glob, codes in table.get("per-file-ignores", {}).items():
        for code in codes:
            require_suppressible_code(code, registry=registry)
        require_live_glob(glob, root=root, scope=scope)
        per_file_ignores.append(PerFileIgnore(glob=glob, codes=frozenset(codes)))

    return Config(root=root, registry=resolved, per_file_ignores=per_file_ignores)


def require_known_code(code: str, *, registry: Registry) -> None:
    """Raise `ConfigError` unless the code names a rule in the full registry."""
    if code not in registry.by_code:
        message = f"unknown rule code in configuration: {code}"
        raise ConfigError(message)


def require_suppressible_code(code: str, *, registry: Registry) -> None:
    """Raise `ConfigError` unless the code names a per-file-suppressible rule.

    A project-scope rule sees the whole tree at once, so a per-file glob has
    nothing to bite on — the runner never applies `per-file-ignores` to it. Left
    to validate as a known code it would load yet silently do nothing; strict
    config treats that no-op as the misconfiguration it is. `ignore` is the only
    lever for project-scope rules.
    """
    require_known_code(code, registry=registry)
    if isinstance(registry.by_code[code], ProjectRule):
        message = f"project-scope rule {code} cannot be silenced per-file; use ignore"
        raise ConfigError(message)


def resolve_options(
    tables: dict[str, dict[str, Any]], *, registry: Registry
) -> dict[str, object]:
    """Validate each `[rules.<CODE>]` table and return baked-in Options per code.

    Each table is checked against the rule's `Options` schema: the code must be
    known, the rule must be configurable (have an `options` field), and every key
    must be a declared option with a value of the right type. Keys convert
    kebab→snake. The override is baked with `dataclasses.replace`; the rule's own
    `check` never sees raw config (ADR-0007).
    """
    baked: dict[str, object] = {}
    for code, override in tables.items():
        require_known_code(code, registry=registry)
        rule = registry.by_code[code]
        current = rule_options(rule, code=code)
        option_fields = {field.name: field for field in fields(current)}
        values = {}
        for key, value in override.items():
            name = key.replace("-", "_")
            if name not in option_fields:
                message = f"unknown option for {code}: {key}"
                raise ConfigError(message)
            expected = type(getattr(current, name))
            if not isinstance(value, expected) or isinstance(value, bool) != (
                expected is bool
            ):
                message = (
                    f"option {key} for {code} must be {expected.__name__}, "
                    f"got {type(value).__name__}"
                )
                raise ConfigError(message)
            values[name] = value
        baked[code] = replace(current, **values)
    return baked


def rule_options(rule: Rule, *, code: str) -> Any:  # noqa: ANN401
    """Return a configurable rule's Options, or raise if the rule takes none."""
    options = getattr(rule, "options", None)
    if options is None:
        message = f"rule {code} takes no options"
        raise ConfigError(message)
    return options


def require_live_glob(glob: str, *, root: Path, scope: GitScope) -> None:
    """Raise `ConfigError` unless the glob matches at least one project file.

    "The project" is the whole tree under root — `gather_files([root])`, not the
    files a given run lints — so partial runs never trip on globs aimed at trees
    they aren't linting (ADR-0008). The same `scope` exclusion a run applies is
    threaded here, so the liveness universe excludes `.venv`/gitignored trees.
    """
    for file in gather_files(paths=[root], scope=scope):
        if relative_posix(file, root=root).full_match(glob):
            return
    message = f"per-file-ignores glob matches no files: {glob}"
    raise ConfigError(message)
