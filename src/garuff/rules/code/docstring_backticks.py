"""GAC004 — docstrings use single backticks, never double."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import docstring_node
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator

DOUBLE_BACKTICK = "`" * 2  # avoid a literal double backtick in this file


class DocstringBackticks(SourceRule):
    """Flag a docstring containing double backticks."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each docstring using double backticks."""
        for node in ast.walk(module):
            doc = docstring_node(node)
            if (
                doc is not None
                and isinstance(doc.value, str)
                and DOUBLE_BACKTICK in doc.value
            ):
                yield Violation(
                    rule=self,
                    location=Location.from_node(doc, path=path),
                    detail="use single backticks in docstrings, not double",
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
