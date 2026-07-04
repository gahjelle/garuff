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

    from garuff.violation import Violation


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
