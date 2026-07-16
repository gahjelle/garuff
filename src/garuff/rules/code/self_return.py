"""GAC006 — return `Self`, not a string forward-ref to the enclosing class."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import classes
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


class SelfReturn(SourceRule):
    """Flag a method returning a string forward-ref to its enclosing class."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each forward-ref return to the enclosing class."""
        for cls in classes(module):
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                returns = method.returns
                if isinstance(returns, ast.Constant) and returns.value == cls.name:
                    yield Violation(
                        rule=self,
                        location=Location.from_node(returns, path=path),
                        detail=f'return `Self`, not the forward-ref `"{cls.name}"`',
                    )


SELF_RETURN = SelfReturn(
    code="GAC006",
    summary="return `Self`, not a string forward-ref to the enclosing class",
    rationale="""
        A `"ClassName"` string forward-ref names the class explicitly, so it
        silently lies after a rename and does not follow into subclasses.
        `typing.Self` means "this class" and tracks subclassing.
    """,
    fix="""
        Return `Self` (from `typing`):
            def clone(self) -> "Widget": ...  # before
            def clone(self) -> Self: ...      # after
    """,
)
