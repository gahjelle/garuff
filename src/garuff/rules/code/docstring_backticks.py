"""GAC004 — docstrings use single backticks, never double."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.fixes import line_starts, node_span
from garuff.rule import SourceRule
from garuff.rules.code.syntax import docstring_node
from garuff.schemas import Edit, Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator

DOUBLE_BACKTICK = "`" * 2  # avoid a literal double backtick in this file


def double_backtick_docstrings(module: ast.Module) -> Iterator[ast.Constant]:
    """Yield each docstring `Constant` in the module that uses double backticks."""
    for node in ast.walk(module):
        doc = docstring_node(node)
        if (
            doc is not None
            and isinstance(doc.value, str)
            and DOUBLE_BACKTICK in doc.value
        ):
            yield doc


class DocstringBackticks(SourceRule):
    """Flag a docstring containing double backticks."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each docstring using double backticks."""
        for doc in double_backtick_docstrings(module):
            yield Violation(
                rule=self,
                location=Location.from_node(doc, path=path),
                detail="use single backticks in docstrings, not double",
            )

    def edits(self, module: ast.Module, *, text: str, path: Path) -> Iterator[Edit]:
        """Yield an Edit collapsing each double backtick pair to a single one.

        Shares `double_backtick_docstrings` with `check`. Operates on the raw
        literal segment (quotes/prefix included), not `doc.value`, so it is safe
        inside any string form (`r`, `f`, triple) — only double-backtick runs are
        touched, so it is idempotent.
        """
        starts = line_starts(text)
        for doc in double_backtick_docstrings(module):
            start, end = node_span(doc, starts=starts)
            original = text[start:end]
            yield Edit(
                location=Location.from_node(doc, path=path),
                start=start,
                end=end,
                original=original,
                replacement=original.replace(DOUBLE_BACKTICK, "`"),
            )


DOCSTRING_BACKTICKS = DocstringBackticks(
    code="GAC004",
    summary="use single backticks in docstrings, never double",
    rationale="""
        Double backticks are reStructuredText inline-literal syntax; garuff's
        docstrings are plain prose where a single backtick marks code, so a
        double pair just renders as stray backticks.
    """,
    fix="""
        Collapse the pair to one on each side:
            \"\"\"Return the ``value``.\"\"\"   # before
            \"\"\"Return the `value`.\"\"\"     # after
    """,
)
