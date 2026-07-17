"""Output — terse locator lines and the agent-facing explanation block."""

import textwrap
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garuff.explain import ExplainedRule
    from garuff.rule import Explanation
    from garuff.schemas import DirectiveError, ParseFailure, Violation


class Verbosity(IntEnum):
    """How much of garuff's own output to print — an ordered scale.

    Ordered low-to-high: quieter levels compare *less than* louder ones, so
    output gates read as thresholds (`verbosity >= Verbosity.DEFAULT`). Only the
    two shipped levels exist today; `SILENT` (below `QUIET`) and `VERBOSE`
    (above `DEFAULT`) are the reserved ends — see ADR-0016 and #42.
    """

    QUIET = 0
    DEFAULT = 1


# The label gutter: each `why`/`fix`/`note` label is right-aligned in this many
# columns, then two spaces, then the field's text. Continuation lines align
# under the text (a `GUTTER + 2`-space hang), preserving an author's own indent.
GUTTER = 6

# Every appendix line is indented this far, so a column-0 line stays a finding
# (ADR-0012). Blocks are separated by one blank line.
APPENDIX_INDENT = "  "


def render_field(label: str, *, text: str) -> list[str]:
    """Render one labelled field as its gutter line plus aligned continuations."""
    hang = " " * (GUTTER + 2)
    lines = text.split("\n")
    rendered = [f"{label.rjust(GUTTER)}  {lines[0]}"]
    rendered += [hang + line if line else "" for line in lines[1:]]
    return rendered


def render_explanation(explanation: Explanation, *, note: str | None = None) -> str:
    """Render one rule's block: header, why, fix, and an optional note.

    The header is `CODE` + two spaces + summary; `why` and `fix` follow in the
    gutter. A `note` — only ever supplied by `garuff rule` for an ignored rule —
    is a fourth labelled line; the appendix never passes one.
    """
    lines = [f"{explanation.code}  {explanation.summary}"]
    lines += render_field("why", text=explanation.rationale)
    lines += render_field("fix", text=explanation.fix)
    if note is not None:
        lines += render_field("note", text=note)
    return "\n".join(lines)


def render_explanations(explained: list[ExplainedRule]) -> str:
    """Render each already-selected rule as a block, one blank line between them."""
    return "\n\n".join(
        render_explanation(rule.explanation, note=rule.note) for rule in explained
    )


def render_appendix(explained: list[ExplainedRule]) -> str:
    """Render the check Appendix: one indented block per already-selected rule.

    `explained` is the distinct fired rules chosen by `explain.appendix_rules`;
    each block is indented two spaces so it never occupies column 0 (ADR-0012).
    Returns `""` for an empty list, so the CLI writes nothing.
    """
    return "\n\n".join(
        textwrap.indent(
            render_explanation(rule.explanation, note=rule.note), APPENDIX_INDENT
        )
        for rule in explained
    )


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
    fixes: int | None = None,
) -> str:
    """Render the one-line run summary for stderr, split by file extension.

    Directive errors are counted separately from violations — they are not rule
    findings (ADR-0011) — and named only when there are any. `fixes` is `None`
    on a normal run (the clause is omitted, so no `0 fixes` noise) and set on a
    `--fix` run even at `0`, where it precedes the violations count. Its plural
    is irregular (`fix`/`fixes`), so it does not go through `plural_suffix`.
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
    summary += ": "
    if fixes is not None:
        summary += f"{fixes} {'fix' if fixes == 1 else 'fixes'}, "
    summary += f"{violations} violation{plural_suffix(violations)}"
    if directive_errors:
        errors = f"{directive_errors} directive error{plural_suffix(directive_errors)}"
        summary += f", {errors}"
    return summary


def plural_suffix(count: int) -> str:
    """Return the plural suffix for a count."""
    return "" if count == 1 else "s"
