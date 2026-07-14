"""Rule identity: the required agent-facing text and its normalization.

A rule carries three text fields — `summary`, `rationale`, `fix` — as part of
its identity (ADR-0004). All three are required, so a ported rule cannot forget
to explain itself, and all three are `inspect.cleandoc`-normalized at
construction, so an author writes an indented triple-quoted literal and stores
print-ready text without importing `cleandoc`.
"""

import pytest

from garuff.rule import Rule


def test_rule_requires_rationale_and_fix() -> None:
    """A rule built without `rationale`/`fix` is a TypeError at construction."""
    with pytest.raises(TypeError):
        Rule(code="GAX001", summary="a rule")  # ty: ignore[missing-argument]


def test_rule_cleandoc_normalizes_the_text() -> None:
    """An indented triple-quoted literal is stored dedented and stripped."""
    rule = Rule(
        code="GAX001",
        summary="a rule",
        rationale="""
            first line
            second line
        """,
        fix="""
            do the thing
        """,
    )

    assert rule.rationale == "first line\nsecond line"
    assert rule.fix == "do the thing"
