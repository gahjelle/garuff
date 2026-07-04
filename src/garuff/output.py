"""Output — terse locator lines for each violation."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.schemas import ParseFailure, Violation


def render_violations(*, violations: list[Violation], root: Path) -> str:
    """Render each violation as a locator line, joined by newlines."""
    return "\n".join(violation.render(root=root) for violation in violations)


def render_parse_failures(*, failures: list[ParseFailure], root: Path) -> str:
    """Render each unparsable file as a `path:line:col: could not parse` line."""
    return "\n".join(failure.render(root=root) for failure in failures)


# Display order for the per-extension counts. `.py` comes last so the parse
# `(N skipped)` note — which only ever counts `.py` files — sits next to it.
SUMMARY_SUFFIX_ORDER = (".md", ".py")


def render_summary(
    *, linted_by_suffix: dict[str, int], skipped: int, violations: int
) -> str:
    """Render the one-line run summary for stderr, split by file extension."""
    extras = sorted(linted_by_suffix.keys() - set(SUMMARY_SUFFIX_ORDER))
    counts = [
        f"{count} {suffix} file{plural_suffix(count)}"
        for suffix in (*SUMMARY_SUFFIX_ORDER, *extras)
        if (count := linted_by_suffix.get(suffix, 0))
    ]
    files = ", ".join(counts) if counts else "0 files"
    summary = f"{files} linted"
    if skipped:
        summary += f" ({skipped} skipped)"
    return f"{summary}: {violations} violation{plural_suffix(violations)}"


def plural_suffix(count: int) -> str:
    """Return the plural suffix for a count."""
    return "" if count == 1 else "s"
