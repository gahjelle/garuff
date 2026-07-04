"""Project discovery — locate the root by walking up to a pyproject.toml."""

from pathlib import Path


class ProjectNotFoundError(Exception):
    """No pyproject.toml was found walking up from the starting directory."""


def discover_root(*, start: Path) -> Path:
    """Return the nearest ancestor of start containing a pyproject.toml."""
    for directory in [start, *start.parents]:
        if (directory / "pyproject.toml").is_file():
            return directory
    message = f"no pyproject.toml found walking up from {start}"
    raise ProjectNotFoundError(message)
