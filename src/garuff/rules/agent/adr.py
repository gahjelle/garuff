"""Shared ADR-file recognition and grouping for the GAA project rules."""

import re
from pathlib import Path

# A 4-digit numeric prefix followed by a dash and the ADR's slug. Revisit if
# the project ever widens the prefix.
ADR_NAME_RE = re.compile(r"^(\d{4})-.*\.md$")


def iter_adr_groups(project_files: list[Path]) -> dict[Path, list[tuple[int, Path]]]:
    """Group ADR files by their containing `docs/adr/` directory.

    Returns `{adr_dir: [(number, path), ...]}`, sorted for deterministic output.
    """
    groups: dict[Path, list[tuple[int, Path]]] = {}
    for path in sorted(project_files):
        match = ADR_NAME_RE.match(path.name)
        if not match or path.parent.name != "adr" or path.parent.parent.name != "docs":
            continue
        number = int(match.group(1))
        groups.setdefault(path.parent, []).append((number, path))
    return groups
