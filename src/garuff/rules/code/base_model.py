"""GAC002 — models inherit `FrozenModel` or `StrictModel`, never `BaseModel`.

A class subclassing `BaseModel` directly opts out of the project's strict/frozen
defaults; the two project bases bake those in. The bases themselves are exempt.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.rules.code.syntax import classes, is_named
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

BASE_CLASSES = frozenset({"FrozenModel", "StrictModel"})


class BaseModelInheritance(SourceRule):
    """Flag a model class inheriting `BaseModel` directly."""

    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each class subclassing `BaseModel` directly."""
        for node in classes(module):
            if node.name in BASE_CLASSES:
                continue
            if any(is_named(base, name="BaseModel") for base in node.bases):
                yield Violation(
                    rule=self,
                    location=Location.from_node(node, path=path),
                    detail=(
                        f"`{node.name}` must subclass `StrictModel` or "
                        f"`FrozenModel`, not `BaseModel`"
                    ),
                )


BASE_MODEL_INHERITANCE = BaseModelInheritance(
    code="GAC002",
    summary="models inherit `FrozenModel` or `StrictModel`, never `BaseModel`",
    rationale="""
        A model that subclasses `BaseModel` directly opts out of the project's
        strict-and-frozen defaults — silent mutability and lax validation slip
        back in. `FrozenModel`/`StrictModel` carry those defaults for every model.
    """,
    fix="""
        Subclass the project's strict base instead:
            class User(BaseModel): ...    # before
            class User(FrozenModel): ...  # after
    """,
)
