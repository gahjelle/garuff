"""Passive result and value types — the located, renderable outcomes of a run.

This module is the low-dependency home for the data garuff produces: the
`Location` value object, the `Violation` and `ParseFailure` that carry one, and
the `RunResult` aggregate. The behaviour-carrying `Rule` hierarchy deliberately
lives elsewhere (`rule.py`); see ADR-0004.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from garuff.rule import Rule


def display_path(path: Path, *, root: Path) -> str:
    """Render a path relative to root, falling back to its absolute form."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


@dataclass(kw_only=True)
class Location:
    """A position in a source file."""

    path: Path
    line: int
    col: int

    @classmethod
    def from_offset(cls, *, text: str, offset: int, path: Path) -> Self:
        """Locate a character offset in `text` as a 1-based line/col Location."""
        line = text.count("\n", 0, offset) + 1
        col = offset - text.rfind("\n", 0, offset)
        return cls(path=path, line=line, col=col)

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col`, path relative to root."""
        return f"{display_path(self.path, root=root)}:{self.line}:{self.col}"


@dataclass(kw_only=True)
class Violation:
    """A single instance of a rule being broken at a specific location."""

    rule: Rule
    location: Location

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: CODE summary`, path relative to root."""
        return (
            f"{self.location.render(root=root)}: {self.rule.code} {self.rule.summary}"
        )


@dataclass(kw_only=True)
class ParseFailure:
    """A file that could not be parsed, with the location of the failure."""

    location: Location
    message: str

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: could not parse: message`."""
        return f"{self.location.render(root=root)}: could not parse: {self.message}"


@dataclass(kw_only=True)
class RunResult:
    """The outcome of a run: violations found, files linted, and files skipped."""

    violations: list[Violation]
    linted_by_suffix: dict[str, int]
    parse_failures: list[ParseFailure] = field(default_factory=list)

    @property
    def linted(self) -> int:
        """How many files were linted, across every extension."""
        return sum(self.linted_by_suffix.values())

    @property
    def skipped(self) -> int:
        """How many files were skipped because they could not be parsed."""
        return len(self.parse_failures)
