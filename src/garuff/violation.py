"""The Violation value object and its terse locator rendering."""

from dataclasses import dataclass
from pathlib import Path

from garuff.rule import Rule


def display_path(path: Path, *, root: Path) -> str:
    """Render a path relative to root, falling back to its absolute form."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


@dataclass(kw_only=True)
class Violation:
    """A single instance of a rule being broken at a specific location."""

    rule: Rule
    path: Path
    line: int
    col: int

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: CODE summary`, path relative to root."""
        location = f"{display_path(self.path, root=root)}:{self.line}:{self.col}"
        return f"{location}: {self.rule.code} {self.rule.summary}"
