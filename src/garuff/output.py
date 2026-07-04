"""Output — terse locator lines for each violation."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.runner import ParseFailure
    from garuff.violation import Violation


def render_violations(*, violations: list[Violation], root: Path) -> str:
    """Render each violation as a locator line, joined by newlines."""
    return "\n".join(violation.render(root=root) for violation in violations)


def render_parse_failures(*, failures: list[ParseFailure], root: Path) -> str:
    """Render each unparseable file as a `path:line:col: could not parse` line."""
    return "\n".join(failure.render(root=root) for failure in failures)


def render_summary(*, linted: int, skipped: int, violations: int) -> str:
    """Render the one-line run summary for stderr."""
    files = f"{linted} .py-file{plural_suffix(linted)} linted"
    if skipped:
        files += f" ({skipped} skipped)"
    return f"{files}: {violations} violation{plural_suffix(violations)}"


def plural_suffix(count: int) -> str:
    """Return the plural suffix for a count."""
    return "" if count == 1 else "s"
