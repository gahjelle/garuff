"""Project discovery — locate the root by walking up to a pyproject.toml."""

from pathlib import Path

from garuff.exceptions import ProjectNotFoundError


def discover_root(*, start: Path) -> Path:
    """Return the nearest ancestor of start containing a pyproject.toml."""
    for directory in [start, *start.parents]:
        if (directory / "pyproject.toml").is_file():
            return directory
    message = f"no pyproject.toml found walking up from {start}"
    raise ProjectNotFoundError(message)
