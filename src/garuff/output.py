"""Output — terse locator lines for each violation."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.violation import Violation


def render_violations(*, violations: list[Violation], root: Path) -> str:
    """Render each violation as a locator line, joined by newlines."""
    return "\n".join(violation.render(root=root) for violation in violations)


def render_summary(*, linted: int, skipped: int, violations: int) -> str:
    """Render the one-line run summary for stderr."""
    files = f"{linted} .py-file{_s(linted)} linted"
    if skipped:
        files += f" ({skipped} skipped)"
    return f"{files}: {violations} violation{_s(violations)}"


def _s(count: int) -> str:
    """Return the plural suffix for a count."""
    return "" if count == 1 else "s"
