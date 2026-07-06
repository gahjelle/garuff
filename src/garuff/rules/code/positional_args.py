"""GAC008 — at most one positional parameter.

Positional parameters past the first make a call site ambiguous — the reader has
to count arguments to know what each means. Beyond the limit, extra parameters
belong after a bare `*`, forcing callers to name them. This is the worked example
of a *configurable* rule: `max_positional_args` (default 1) tunes the ceiling,
baked in by `config.load` before the run (ADR-0007).

Counting is structural. A parameter is positional if it is posonly or normal;
keyword-only params, `*args`, and `**kwargs` never count. A method's first
positional (`self`/`cls`) is exempt — detected by the function being a direct
child of a `ClassDef` — unless it is a `@staticmethod`. Lambdas are not checked.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator

type Function = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(kw_only=True)
class PositionalArgsOptions:
    """Options for GAC008: the maximum positional parameters a function may take."""

    max_positional_args: int = 1


def iter_functions(node: ast.AST, *, in_class: bool) -> Iterator[tuple[Function, bool]]:
    """Yield every function under node, paired with whether it is a class method.

    A function is a method when its immediate container is a `ClassDef`; a
    function nested inside another function is not, so descending through a
    function body resets the flag.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            yield child, in_class
            yield from iter_functions(child, in_class=False)
        elif isinstance(child, ast.ClassDef):
            yield from iter_functions(child, in_class=True)
        else:
            yield from iter_functions(child, in_class=in_class)


def is_staticmethod(function: Function) -> bool:
    """Report whether the function carries a bare `@staticmethod` decorator."""
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
        for decorator in function.decorator_list
    )


def positional_count(function: Function, *, is_method: bool) -> int:
    """Count the function's positional parameters, exempting a method's first."""
    count = len(function.args.posonlyargs) + len(function.args.args)
    if is_method and not is_staticmethod(function):
        count -= 1
    return count


@dataclass(kw_only=True)
class PositionalArgs(SourceRule):
    """Flag any function taking more positional parameters than the option allows."""

    options: PositionalArgsOptions = field(default_factory=PositionalArgsOptions)

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each function over the positional-arg ceiling."""
        limit = self.options.max_positional_args
        for function, is_method in iter_functions(module, in_class=False):
            count = positional_count(function, is_method=is_method)
            if count > limit:
                yield Violation(
                    rule=self,
                    location=Location(
                        path=path,
                        line=function.lineno,
                        col=function.col_offset + 1,
                    ),
                    detail=(
                        f"`{function.name}` takes {count} positional parameters "
                        f"(at most {limit})"
                    ),
                )


POSITIONAL_ARGS = PositionalArgs(
    code="GAC008",
    summary="at most one positional parameter",
    options=PositionalArgsOptions(),
)
