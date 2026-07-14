"""The resolved Config's catalog/active split, tested at the `load` seam.

`Config.registry` is the full catalog — every known rule, options baked, even a
globally-ignored one — so an ignored rule stays explainable by `garuff rule`.
`Config.active` drops the ignored rules; it is what the runner runs. This
structural contract is what `cli.explain` consumes, so it is asserted directly
on the resolved Config rather than only through a lint run.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff.config import load
from garuff.files import GitScope
from garuff.rules import REGISTRY

if TYPE_CHECKING:
    from collections.abc import Callable


def test_ignored_rule_stays_in_the_catalog_but_leaves_active(
    *, project: Callable[[dict[str, str]], Path]
) -> None:
    """`ignore = ["GAC001"]` keeps GAC001 in the catalog, drops it from active."""
    root = project(
        {
            "pyproject.toml": (
                '[project]\nname = "sample"\n[tool.garuff]\nignore = ["GAC001"]\n'
            ),
        }
    )

    config = load(root=root, registry=REGISTRY, scope=GitScope(allowed=None))

    assert "GAC001" in config.registry.by_code
    assert "GAC001" not in config.active.by_code
    assert config.known_codes == frozenset(config.registry.by_code)
