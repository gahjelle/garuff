"""GAC007 — ruff-exempt modules stay at runtime, not under `TYPE_CHECKING`.

ruff's `flake8-type-checking.exempt-modules` are declared safe to import at
runtime; hiding one under `if TYPE_CHECKING:` removes its names at runtime for no
benefit. The exempt set is a garuff option (`exempt-modules`), default empty, so
the rule is inert until a project configures it (ADR-0015). Configurable rule #2.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(kw_only=True)
class TypeCheckingExemptOptions:
    """Options for GAC007: the ruff-exempt modules that must stay at runtime."""

    exempt_modules: list[str] = field(default_factory=list)


def type_checking_imports(module: ast.Module) -> Iterator[ast.ImportFrom]:
    """Yield each `from ... import ...` directly under an `if TYPE_CHECKING:` block."""
    for node in ast.walk(module):
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        ):
            for stmt in node.body:
                if isinstance(stmt, ast.ImportFrom):
                    yield stmt


@dataclass(kw_only=True)
class TypeCheckingExempt(SourceRule):
    """Flag a ruff-exempt module imported under `TYPE_CHECKING`."""

    options: TypeCheckingExemptOptions = field(
        default_factory=TypeCheckingExemptOptions
    )

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each exempt module imported under TYPE_CHECKING."""
        exempt = set(self.options.exempt_modules)
        for stmt in type_checking_imports(module):
            if stmt.module in exempt:
                yield Violation(
                    rule=self,
                    location=Location.from_node(stmt, path=path),
                    detail=f"move `{stmt.module}` out of `TYPE_CHECKING`; it is exempt",
                )


TYPE_CHECKING_EXEMPT = TypeCheckingExempt(
    code="GAC007",
    summary="keep a ruff-exempt module at runtime, not under `TYPE_CHECKING`",
    rationale="""
        A module in ruff's `flake8-type-checking` exempt list is meant to be
        imported at runtime; hiding it under `if TYPE_CHECKING:` makes its names
        unavailable at runtime for nothing. The exempt set is configured under
        `[tool.garuff.rules.GAC007]`.
    """,
    fix="""
        Move the import above the `if TYPE_CHECKING:` block:
            if TYPE_CHECKING:
                from pathlib import Path   # before — move it up
            from pathlib import Path       # after — a runtime import
    """,
    options=TypeCheckingExemptOptions(),
)
