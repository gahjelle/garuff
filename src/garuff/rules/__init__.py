"""Explicit aggregation of every rule into the registry (no auto-discovery)."""

from garuff.registry import Registry
from garuff.rules.code.future_import import FUTURE_ANNOTATIONS_IMPORT
from garuff.rules.code.possessive_prefix import POSSESSIVE_PREFIX

REGISTRY = Registry(rules=[FUTURE_ANNOTATIONS_IMPORT, POSSESSIVE_PREFIX])

__all__ = ["REGISTRY"]
