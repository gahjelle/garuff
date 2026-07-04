"""Explicit aggregation of every rule into the registry (no auto-discovery)."""

from garuff.registry import Registry
from garuff.rules.code.future_import import FUTURE_ANNOTATIONS_IMPORT

REGISTRY = Registry(rules=[FUTURE_ANNOTATIONS_IMPORT])

__all__ = ["REGISTRY"]
