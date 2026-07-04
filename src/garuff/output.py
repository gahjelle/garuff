"""Output — terse locator lines for each violation."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.violation import Violation


def render_violations(*, violations: list[Violation], root: Path) -> str:
    """Render each violation as a locator line, joined by newlines."""
    return "\n".join(violation.render(root=root) for violation in violations)
