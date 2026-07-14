"""Rule base classes — the self-describing unit garuff enforces.

`Rule` holds the scope-independent identity and explanation; each scope subclass
adds a `check` for the kind of input it consumes. See ADR-0003.
"""

import abc
from dataclasses import dataclass
from inspect import cleandoc
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from garuff.schemas import Violation


@dataclass(kw_only=True)
class Rule:
    """A single convention garuff enforces, identified by a stable code.

    Carries the rule's agent-facing text in three required parts: `summary`
    (the terse default per-violation line), `rationale` (why the convention
    exists), and `fix` (the prescribed correct form). All three are
    `inspect.cleandoc`-normalized in `__post_init__`, so an author writes an
    indented triple-quoted literal and never imports `cleandoc`. A subclass that
    adds its own `__post_init__` must call `super().__post_init__()`.
    """

    code: str
    summary: str
    rationale: str
    fix: str

    def __post_init__(self) -> None:
        """Normalize the agent-facing text to print-ready form."""
        self.summary = cleandoc(self.summary)
        self.rationale = cleandoc(self.rationale)
        self.fix = cleandoc(self.fix)


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
