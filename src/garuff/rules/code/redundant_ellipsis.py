"""GAC003 — a `Protocol` method's `...` body is redundant; the docstring is enough.

Scoped to `Protocol` methods today. Named generally so a later issue can broaden
it to other redundant `...` bodies (empty exception/marker classes) under the
same code.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import classes, is_named
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


def ellipsis_statements(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[ast.Expr]:
    """Yield each bare `...` expression statement in the method body."""
    for stmt in method.body:
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis
        ):
            yield stmt


class RedundantEllipsis(SourceRule):
    """Flag a `...` statement in a `Protocol` method."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `...` statement in a Protocol method."""
        for node in classes(module):
            if not any(is_named(base, name="Protocol") for base in node.bases):
                continue
            for method in node.body:
                if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                    for stmt in ellipsis_statements(method):
                        yield Violation(
                            rule=self,
                            location=Location.from_node(stmt, path=path),
                            detail=(
                                "drop `...` from the Protocol method; "
                                "the docstring is enough"
                            ),
                        )


REDUNDANT_ELLIPSIS = RedundantEllipsis(
    code="GAC003",
    summary="drop `...` from a `Protocol` method; the docstring is body enough",
    rationale="""
        Once a `Protocol` method carries a docstring, its `...` placeholder is
        dead weight — the docstring is already a complete body.
    """,
    fix="""
        Delete the `...` line, leaving the docstring as the body:
            class Reader(Protocol):
                def read(self) -> bytes:
                    \"\"\"Return the payload.\"\"\"
                    ...   # before — delete this line
    """,
)
