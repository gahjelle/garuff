"""Shared AST selectors for the GAC (code) rules — twin of `rules/agent/adr.py`.

Traversal the code rules reuse rather than each re-walking the tree. `functions`
yields every function in a module — nested ones included — paired with whether it
is a class method, the one piece of context a plain `ast.walk` cannot supply.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["Function", "functions"]

type Function = ast.FunctionDef | ast.AsyncFunctionDef


def functions(module: ast.Module) -> Iterator[tuple[Function, bool]]:
    """Yield every function under module, paired with whether it is a method.

    A function is a method when its immediate container is a `ClassDef`; a
    function nested inside another function is not, so descending through a
    function body resets the flag. Nested functions are yielded too.
    """

    def walk(node: ast.AST, *, in_class: bool) -> Iterator[tuple[Function, bool]]:
        """Recurse node's children, tracking whether the current scope is a class."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                yield child, in_class
                yield from walk(child, in_class=False)
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, in_class=True)
            else:
                yield from walk(child, in_class=in_class)

    yield from walk(module, in_class=False)
