"""The Violation value object and its terse locator rendering."""

from dataclasses import dataclass
from pathlib import Path

from garuff.rule import Rule


@dataclass(kw_only=True)
class Violation:
    """A single instance of a rule being broken at a specific location."""

    rule: Rule
    path: Path
    line: int
    col: int

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: CODE summary`, path relative to root."""
        return (
            f"{self._display_path(root=root)}:{self.line}:{self.col}:"
            f" {self.rule.code} {self.rule.summary}"
        )

    def _display_path(self, *, root: Path) -> str:
        """Render the path relative to root, falling back to absolute."""
        try:
            return str(self.path.relative_to(root))
        except ValueError:
            return str(self.path)
