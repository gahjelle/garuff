"""Rule identity: the required agent-facing text and its normalization.

A rule carries three text fields — `summary`, `rationale`, `fix` — as part of
its identity (ADR-0004). All three are required, so a ported rule cannot forget
to explain itself, and all three are `inspect.cleandoc`-normalized at
construction, so an author writes an indented triple-quoted literal and stores
print-ready text without importing `cleandoc`.
"""

from dataclasses import replace

import pytest

from garuff.rule import Rule
from garuff.rules.code.positional_args import POSITIONAL_ARGS, PositionalArgsOptions


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


def test_explanation_substitutes_baked_option_values() -> None:
    """GAC008's explanation names the configured ceiling, not a placeholder."""
    default = POSITIONAL_ARGS.explanation
    assert default.code == "GAC008"
    assert default.summary == "keep positional parameters to at most 1"
    assert "The limit is 1;" in default.fix

    raised = replace(
        POSITIONAL_ARGS, options=PositionalArgsOptions(max_positional_args=3)
    )
    explanation = raised.explanation
    assert explanation.summary == "keep positional parameters to at most 3"
    assert "The limit is 3;" in explanation.fix


def test_explanation_of_an_optionless_rule_is_unchanged() -> None:
    """A rule with no options renders its text verbatim (nothing to substitute)."""
    rule = Rule(
        code="GAX001",
        summary="a $literal that is not an option",
        rationale="body",
        fix="body",
    )

    assert rule.explanation.summary == "a $literal that is not an option"
