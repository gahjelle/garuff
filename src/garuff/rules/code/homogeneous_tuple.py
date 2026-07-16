"""GAC005 — homogeneous sequences use `list[T]`, not `tuple[T, ...]`."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import is_named
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


def is_variable_length_tuple(node: ast.Subscript) -> bool:
    """Report whether node is a `tuple[T, ...]` subscript."""
    if not is_named(node.value, name="tuple"):
        return False
    sliced = node.slice
    return isinstance(sliced, ast.Tuple) and any(
        isinstance(elt, ast.Constant) and elt.value is Ellipsis for elt in sliced.elts
    )


class HomogeneousTuple(SourceRule):
    """Flag a `tuple[T, ...]` annotation."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `tuple[T, ...]` subscript."""
        for node in ast.walk(module):
            if isinstance(node, ast.Subscript) and is_variable_length_tuple(node):
                yield Violation(
                    rule=self,
                    location=Location.from_node(node, path=path),
                    detail=(
                        "use `list[T]` for homogeneous sequences, not `tuple[T, ...]`"
                    ),
                )


HOMOGENEOUS_TUPLE = HomogeneousTuple(
    code="GAC005",
    summary="homogeneous sequences use `list[T]`, not `tuple[T, ...]`",
    rationale="""
        `tuple[T, ...]` is a variable-length tuple — a homogeneous, immutable
        sequence dressed as a fixed record. `list[T]` states "a sequence of
        unknown length" directly.
    """,
    fix="""
        Swap the annotation:
            def f() -> tuple[int, ...]: ...  # before
            def f() -> list[int]: ...        # after
    """,
)
