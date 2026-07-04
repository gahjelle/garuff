"""The Registry — the central collection of all known rules, looked up by code."""

from dataclasses import dataclass, field

from garuff.exceptions import DuplicateRuleCodeError, UnknownRuleCodeError
from garuff.rule import Rule


@dataclass(kw_only=True)
class Registry:
    """Holds every known rule; the strict authority on rule codes."""

    rules: list[Rule]
    by_code: dict[str, Rule] = field(init=False)

    def __post_init__(self) -> None:
        """Index rules by code, rejecting duplicate codes."""
        by_code: dict[str, Rule] = {}
        for rule in self.rules:
            if rule.code in by_code:
                message = f"duplicate rule code: {rule.code}"
                raise DuplicateRuleCodeError(message)
            by_code[rule.code] = rule
        self.by_code = by_code

    def lookup(self, code: str) -> Rule:
        """Return the rule with this code, or raise if it is unknown."""
        try:
            return self.by_code[code]
        except KeyError:
            message = f"unknown rule code: {code}"
            raise UnknownRuleCodeError(message) from None
