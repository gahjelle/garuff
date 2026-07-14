"""Registry behaviour: the strict authority on rule codes."""

import pytest

from garuff.exceptions import DuplicateRuleCodeError, UnknownRuleCodeError
from garuff.registry import Registry
from garuff.rules import REGISTRY
from garuff.rules.code.future_import import FutureAnnotationsImport


def test_rejects_duplicate_codes() -> None:
    """Two rules sharing a code cannot be registered together."""
    first = FutureAnnotationsImport(
        code="GAC001", summary="first", rationale="", fix=""
    )
    second = FutureAnnotationsImport(
        code="GAC001", summary="second", rationale="", fix=""
    )

    with pytest.raises(DuplicateRuleCodeError, match="GAC001"):
        Registry(rules=[first, second])


def test_lookup_returns_rule_by_code() -> None:
    """A known code resolves to its rule."""
    rule = FutureAnnotationsImport(
        code="GAC001", summary="a rule", rationale="", fix=""
    )
    registry = Registry(rules=[rule])

    assert registry.lookup("GAC001") is rule


def test_lookup_unknown_code_raises() -> None:
    """An unknown code raises rather than returning nothing."""
    registry = Registry(rules=[])

    with pytest.raises(UnknownRuleCodeError):
        registry.lookup("GAC999")


def test_no_explanation_leaves_an_unresolved_placeholder() -> None:
    """Every real rule's rendered text substitutes cleanly — no stray `$` survives.

    `safe_substitute` prints an unknown `$name` verbatim rather than raising
    inside a user's run, so a typo'd placeholder would slip out silently. This
    registry-wide guard catches it at test time instead.
    """
    for rule in REGISTRY.rules:
        explanation = rule.explanation
        for text in (explanation.summary, explanation.rationale, explanation.fix):
            assert "$" not in text, f"{rule.code}: {text!r}"
