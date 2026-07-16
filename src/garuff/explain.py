"""Explaining rules — which rules to teach, and the note for an ignored one.

The domain behind `garuff rule` and the check Appendix: resolve the catalog
(every known rule, options baked) and the active subset for a directory, select
the rule(s) to explain, and attach the ignored-rule note. `cli` renders and
prints what these return and holds no selection logic; `output` renders an
`ExplainedRule` without deciding which rules appear.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.config import resolve
from garuff.exceptions import ProjectNotFoundError
from garuff.rule import Explanation

if TYPE_CHECKING:
    from collections.abc import Callable

    from garuff.registry import Registry
    from garuff.schemas import Violation

# The note `garuff rule` appends to a rule ignored in the project's config.
IGNORED_NOTE = "ignored in this project's configuration"


@dataclass(kw_only=True)
class ExplainedRule:
    """A rule's `Explanation` plus the note (if any) shown alongside it."""

    explanation: Explanation
    note: str | None = None


def resolve_registries(
    *, start: Path, registry: Registry, warn: Callable[[str], object]
) -> tuple[Registry, Registry]:
    """Return the (catalog, active) registries for the project at `start`.

    Inside a project both come from its validated config; outside any project
    both are `registry` unchanged, so a rule still explains at its default
    options. `ConfigError` propagates — the options are unknowable without a
    valid config.
    """
    try:
        config, _ = resolve(start=start, registry=registry, warn=warn)
    except ProjectNotFoundError:
        return registry, registry
    return config.registry, config.active


def note_for(code: str, *, active: Registry) -> str | None:
    """Return the ignored-rule note when `code` is not in the active set."""
    return None if code in active.by_code else IGNORED_NOTE


def explain_rule(code: str, *, catalog: Registry, active: Registry) -> ExplainedRule:
    """Explain one known catalog rule, flagged with a note if it is ignored."""
    rule = catalog.by_code[code]
    return ExplainedRule(
        explanation=rule.explanation, note=note_for(code, active=active)
    )


def explain_catalog(*, catalog: Registry, active: Registry) -> list[ExplainedRule]:
    """Explain every catalog rule, code-sorted, each flagged if ignored."""
    return [
        explain_rule(code, catalog=catalog, active=active)
        for code in sorted(catalog.by_code)
    ]


def appendix_rules(*, violations: list[Violation]) -> list[ExplainedRule]:
    """Explain each distinct rule that fired, code-sorted, with no note.

    Deduplicates the violation stream to one entry per rule — forty violations
    of one rule yield one `ExplainedRule` — so the check Appendix teaches each
    fired rule exactly once (ADR-0012).
    """
    fired = {violation.rule.code: violation.rule for violation in violations}
    return [
        ExplainedRule(explanation=rule.explanation) for _, rule in sorted(fired.items())
    ]
