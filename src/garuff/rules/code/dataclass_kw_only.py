"""GAC009 — `@dataclass(kw_only=True)` so fields can't be passed positionally."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import classes, is_named
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


def dataclass_decorator(node: ast.ClassDef) -> ast.expr | None:
    """Return node's `@dataclass` decorator, or None if it has none."""
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if is_named(target, name="dataclass"):
            return decorator
    return None


def has_kw_only(decorator: ast.expr) -> bool:
    """Report whether a `@dataclass` decorator sets `kw_only=True`."""
    keywords = decorator.keywords if isinstance(decorator, ast.Call) else []
    return any(
        kw.arg == "kw_only"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in keywords
    )


class DataclassKwOnly(SourceRule):
    """Flag a `@dataclass` that is not `kw_only=True`."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each `@dataclass` missing `kw_only=True`."""
        for node in classes(module):
            decorator = dataclass_decorator(node)
            if decorator is not None and not has_kw_only(decorator):
                yield Violation(
                    rule=self,
                    location=Location.from_node(node, path=path),
                    detail=(
                        "decorate `@dataclass(kw_only=True)` so fields "
                        "can't be passed positionally"
                    ),
                )


DATACLASS_KW_ONLY = DataclassKwOnly(
    code="GAC009",
    summary="`@dataclass(kw_only=True)` so fields can't be passed positionally",
    rationale="""
        A positional dataclass ties every call site to field order — inserting
        or reordering a field silently rebinds arguments. `kw_only=True` forces
        each field to be named, so the value object stays safe to evolve.
    """,
    fix="""
        Add `kw_only=True` to the decorator:
            @dataclass               # before
            @dataclass(kw_only=True) # after
    """,
)
