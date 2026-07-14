"""Passive result and value types — the located, renderable outcomes of a run.

This module is the low-dependency home for the data garuff produces: the
`Location` value object, the `Violation`, `ParseFailure` and `DirectiveError`
that carry one, and the `RunResult` aggregate. The behaviour-carrying `Rule`
hierarchy deliberately lives elsewhere (`rule.py`); see ADR-0004.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from garuff import branding
from garuff.rule import Rule


def display_path(path: Path, *, root: Path) -> str:
    """Render a path relative to root, falling back to its absolute form."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


@dataclass(kw_only=True)
class Location:
    """A position in a source file, or a bare directory for project scope."""

    path: Path
    line: int | None = None
    col: int | None = None

    @classmethod
    def from_offset(cls, *, text: str, offset: int, path: Path) -> Self:
        """Locate a character offset in `text` as a 1-based line/col Location."""
        line = text.count("\n", 0, offset) + 1
        col = offset - text.rfind("\n", 0, offset)
        return cls(path=path, line=line, col=col)

    @property
    def sort_key(self) -> tuple[str, int, int]:
        """Sort key placing locations in path, then line, then column order."""
        return (str(self.path), self.line or 0, self.col or 0)

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col`, or bare `path/` when directory-level."""
        if self.line is None:
            return f"{display_path(self.path, root=root)}/"
        return f"{display_path(self.path, root=root)}:{self.line}:{self.col}"


@dataclass(kw_only=True)
class Violation:
    """A single instance of a rule being broken at a specific location."""

    rule: Rule
    location: Location
    detail: str | None = None

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: CODE detail`, falling back to the summary.

        The fallback is the rule's *rendered* summary (option values already
        substituted), so a configurable rule that yields no detail never prints
        a raw `$placeholder` on its locator line.
        """
        text = self.detail or self.rule.explanation.summary
        return f"{self.location.render(root=root)}: {self.rule.code} {text}"


@dataclass(kw_only=True)
class ParseFailure:
    """A file that could not be parsed, with the location of the failure."""

    location: Location
    message: str

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: could not parse: message`."""
        return f"{self.location.render(root=root)}: could not parse: {self.message}"


@dataclass(kw_only=True)
class DirectiveError:
    """An invalid inline suppression directive, located at its marker.

    Code-less by design: there is no rule behind it, so it can be neither
    `ignore`d nor suppressed. See ADR-0011.
    """

    location: Location
    message: str

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: invalid <name> directive: message`."""
        location = self.location.render(root=root)
        return f"{location}: invalid {branding.NAME} directive: {self.message}"


@dataclass(kw_only=True)
class RunResult:
    """The outcome of a run: violations found, files linted, and files skipped."""

    violations: list[Violation]
    linted_by_suffix: dict[str, int]
    parse_failures: list[ParseFailure] = field(default_factory=list)
    directive_errors: list[DirectiveError] = field(default_factory=list)

    @property
    def linted(self) -> int:
        """How many files were linted, across every extension."""
        return sum(self.linted_by_suffix.values())

    @property
    def skipped(self) -> int:
        """How many files were skipped because they could not be parsed."""
        return len(self.parse_failures)
