"""Explicit aggregation of every rule into the registry (no auto-discovery)."""

from garuff.registry import Registry
from garuff.rules.agent.adr_consecutive import ADR_CONSECUTIVE
from garuff.rules.agent.adr_duplicate import ADR_DUPLICATE
from garuff.rules.code.future_import import FUTURE_ANNOTATIONS_IMPORT
from garuff.rules.code.positional_args import POSITIONAL_ARGS
from garuff.rules.code.possessive_prefix import POSSESSIVE_PREFIX

REGISTRY = Registry(
    rules=[
        ADR_CONSECUTIVE,
        ADR_DUPLICATE,
        FUTURE_ANNOTATIONS_IMPORT,
        POSITIONAL_ARGS,
        POSSESSIVE_PREFIX,
    ]
)

__all__ = ["REGISTRY"]
