"""GAC001 — no `from __future__ import annotations`.

Python 3.14 evaluates annotations lazily (PEP 649), so the import is dead weight.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.fixes import line_starts, whole_lines_span
from garuff.rule import SourceRule
from garuff.schemas import Edit, Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


def is_future_annotations(node: ast.stmt) -> bool:
    """Whether `node` is a `from __future__ import annotations` statement."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
    )


class FutureAnnotationsImport(SourceRule):
    """Flag `from __future__ import annotations` at module level."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `__future__` annotations import."""
        for node in module.body:
            if is_future_annotations(node):
                yield Violation(
                    rule=self,
                    location=Location.from_node(node, path=path),
                )

    def edits(self, module: ast.Module, *, text: str, path: Path) -> Iterator[Edit]:
        """Yield an Edit deleting each `__future__` annotations import's line(s).

        Shares `is_future_annotations` with `check`, so the two cannot disagree
        about what is a violation. A future-import sharing a physical line with
        another statement via `;` would have that whole line deleted — such
        imports are vanishingly rare and arguably malformed (documented limit).
        """
        starts = line_starts(text)
        for node in module.body:
            if is_future_annotations(node):
                start, end = whole_lines_span(node, text=text, starts=starts)
                yield Edit(
                    location=Location.from_node(node, path=path),
                    start=start,
                    end=end,
                    original=text[start:end],
                    replacement="",
                )


FUTURE_ANNOTATIONS_IMPORT = FutureAnnotationsImport(
    code="GAC001",
    summary="no `from __future__ import annotations`",
    rationale="""
        Python 3.14 evaluates annotations lazily (PEP 649), so the import is
        dead weight — it buys nothing and every module has to carry it.
    """,
    fix="""
        Delete the import:
            - from __future__ import annotations
    """,
)
