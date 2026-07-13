"""Output — terse locator lines for each finding."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.schemas import DirectiveError, ParseFailure, Violation


def render_findings(
    *,
    violations: list[Violation],
    directive_errors: list[DirectiveError],
    root: Path,
) -> str:
    """Render violations and directive errors as one stream, in location order."""
    findings: list[Violation | DirectiveError] = [*violations, *directive_errors]
    findings.sort(key=lambda finding: finding.location.sort_key)
    return "\n".join(finding.render(root=root) for finding in findings)


def render_parse_failures(*, failures: list[ParseFailure], root: Path) -> str:
    """Render each unparsable file as a `path:line:col: could not parse` line."""
    return "\n".join(failure.render(root=root) for failure in failures)


# Display order for the per-extension counts. `.py` comes last so the parse
# `(N skipped)` note — which only ever counts `.py` files — sits next to it.
SUMMARY_SUFFIX_ORDER = (".md", ".py")


def render_summary(
    *,
    linted_by_suffix: dict[str, int],
    skipped: int,
    violations: int,
    directive_errors: int = 0,
) -> str:
    """Render the one-line run summary for stderr, split by file extension.

    Directive errors are counted separately from violations — they are not rule
    findings (ADR-0011) — and named only when there are any.
    """
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
    summary += f": {violations} violation{plural_suffix(violations)}"
    if directive_errors:
        errors = f"{directive_errors} directive error{plural_suffix(directive_errors)}"
        summary += f", {errors}"
    return summary


def plural_suffix(count: int) -> str:
    """Return the plural suffix for a count."""
    return "" if count == 1 else "s"
