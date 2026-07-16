"""GAC010 — every function, method, and nested function has a docstring."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import docstring_node, functions
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator


class FunctionDocstring(SourceRule):
    """Flag a function, method, or nested function without a docstring."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each function lacking a docstring."""
        for function, _ in functions(module):
            if docstring_node(function) is None:
                yield Violation(
                    rule=self,
                    location=Location.from_node(function, path=path),
                    detail=f"add a docstring to `{function.name}`",
                )


FUNCTION_DOCSTRING = FunctionDocstring(
    code="GAC010",
    summary="every function, method, and nested function has a docstring",
    rationale="""
        A docstring is the one-line contract the next reader — human or agent —
        reads before the body. ruff's `D` rules skip `_`-prefixed and nested
        functions; this rule covers them all.
    """,
    fix="""
        Add at least a one-line docstring:
            def helper(x):                    # before
                return x
            def helper(x):                    # after
                \"\"\"Return x unchanged.\"\"\"
                return x
    """,
)
