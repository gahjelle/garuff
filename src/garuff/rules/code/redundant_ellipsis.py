"""GAC003 — a `Protocol` method's `...` body is redundant; the docstring is enough.

Scoped to `Protocol` methods today. Named generally so a later issue can broaden
it to other redundant `...` bodies (empty exception/marker classes) under the
same code.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.fixes import line_starts, whole_lines_span
from garuff.rule import SourceRule
from garuff.rules.code.syntax import Function, classes, docstring_node, is_named
from garuff.schemas import Edit, Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


def ellipsis_statements(method: Function) -> Iterator[ast.Expr]:
    """Yield each bare `...` expression statement in the method body."""
    for stmt in method.body:
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis
        ):
            yield stmt


def protocol_ellipses(module: ast.Module) -> Iterator[tuple[Function, ast.Expr]]:
    """Yield each `(method, ...-statement)` pair in a `Protocol` class's methods."""
    for node in classes(module):
        if not any(is_named(base, name="Protocol") for base in node.bases):
            continue
        for method in node.body:
            if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                for stmt in ellipsis_statements(method):
                    yield method, stmt


class RedundantEllipsis(SourceRule):
    """Flag a `...` statement in a `Protocol` method."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `...` statement in a Protocol method."""
        for _method, stmt in protocol_ellipses(module):
            yield Violation(
                rule=self,
                location=Location.from_node(stmt, path=path),
                detail=("drop `...` from the Protocol method; the docstring is enough"),
            )

    def edits(self, module: ast.Module, *, text: str, path: Path) -> Iterator[Edit]:
        """Yield an Edit deleting each redundant `...` line — guarded by a docstring.

        Shares `protocol_ellipses` with `check`, but emits an Edit only when the
        method still has a docstring once the `...` is gone; deleting the sole
        body statement would leave an empty suite (`SyntaxError`). An undocumented
        `...` is a real violation `check` still reports (with GAC010 nudging a
        docstring first) — it is simply not auto-fixable.
        """
        starts = line_starts(text)
        for method, stmt in protocol_ellipses(module):
            if docstring_node(method) is None:
                continue
            start, end = whole_lines_span(stmt, text=text, starts=starts)
            yield Edit(
                location=Location.from_node(stmt, path=path),
                start=start,
                end=end,
                original=text[start:end],
                replacement="",
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
