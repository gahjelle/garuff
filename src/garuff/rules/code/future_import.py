"""GAC001 — no `from __future__ import annotations`.

Python 3.14 evaluates annotations lazily (PEP 649), so the import is dead weight.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.violation import Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


class FutureAnnotationsImport(SourceRule):
    """Flag `from __future__ import annotations` at module level."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `__future__` annotations import."""
        for node in module.body:
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "__future__"
                and any(alias.name == "annotations" for alias in node.names)
            ):
                yield Violation(
                    rule=self,
                    path=path,
                    line=node.lineno,
                    col=node.col_offset + 1,
                )


FUTURE_ANNOTATIONS_IMPORT = FutureAnnotationsImport(
    code="GAC001",
    summary="no `from __future__ import annotations`",
)
