"""Explicit aggregation of every rule into the registry (no auto-discovery)."""

from garuff.registry import Registry
from garuff.rules.agent.adr_consecutive import ADR_CONSECUTIVE
from garuff.rules.agent.adr_duplicate import ADR_DUPLICATE
from garuff.rules.code.base_model import BASE_MODEL_INHERITANCE
from garuff.rules.code.dataclass_kw_only import DATACLASS_KW_ONLY
from garuff.rules.code.docstring_backticks import DOCSTRING_BACKTICKS
from garuff.rules.code.function_docstring import FUNCTION_DOCSTRING
from garuff.rules.code.future_import import FUTURE_ANNOTATIONS_IMPORT
from garuff.rules.code.homogeneous_tuple import HOMOGENEOUS_TUPLE
from garuff.rules.code.positional_args import POSITIONAL_ARGS
from garuff.rules.code.possessive_prefix import POSSESSIVE_PREFIX
from garuff.rules.code.redundant_ellipsis import REDUNDANT_ELLIPSIS
from garuff.rules.code.self_return import SELF_RETURN

REGISTRY = Registry(
    rules=[
        ADR_CONSECUTIVE,
        ADR_DUPLICATE,
        BASE_MODEL_INHERITANCE,
        DATACLASS_KW_ONLY,
        DOCSTRING_BACKTICKS,
        FUNCTION_DOCSTRING,
        FUTURE_ANNOTATIONS_IMPORT,
        HOMOGENEOUS_TUPLE,
        POSITIONAL_ARGS,
        POSSESSIVE_PREFIX,
        REDUNDANT_ELLIPSIS,
        SELF_RETURN,
    ]
)

__all__ = ["REGISTRY"]
