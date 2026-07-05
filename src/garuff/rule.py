"""Rule base classes — the self-describing unit garuff enforces.

`Rule` holds the scope-independent identity and explanation; each scope subclass
adds a `check` for the kind of input it consumes. See ADR-0003.
"""

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from garuff.schemas import Violation


@dataclass(kw_only=True)
class Rule:
    """A single convention garuff enforces, identified by a stable code."""

    code: str
    summary: str


@dataclass(kw_only=True)
class SourceRule(Rule, abc.ABC):
    """A rule that consumes one parsed Python module (AST) at a time."""

    @abc.abstractmethod
    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the module."""


@dataclass(kw_only=True)
class TextRule(Rule, abc.ABC):
    """A rule that consumes the raw text of one linted file, any extension."""

    @abc.abstractmethod
    def check(self, text: str, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the text."""


@dataclass(kw_only=True)
class ProjectRule(Rule, abc.ABC):
    """A rule that consumes the gathered project file list, checked once."""

    @abc.abstractmethod
    def check(self, project_files: list[Path]) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the project."""
