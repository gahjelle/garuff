"""Inline suppression — extract `# garuff: ignore[...]` directives from a .py file.

Directives are found by scanning tokenize COMMENT tokens, so a marker inside a
string literal never false-matches. Each well-formed marker adds its codes to its
own physical line's suppression set; matching is strictly line-to-line. A marker
naming an unknown code becomes a `DirectiveError`. Validation consults the full
known-code set, not the resolved registry, so a globally-ignored — but real —
code is a silent no-op rather than an error. See ADR-0001, ADR-0011, and
CONTEXT.md (**Directive**).
"""

import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.schemas import DirectiveError, Location

if TYPE_CHECKING:
    from garuff.schemas import Violation

# The marker may sit anywhere in a comment, so it can share a line with another
# tool's pragma. The lookbehind keeps it from matching the tail of a longer word.
MARKER = re.compile(r"(?<![\w])garuff:\s*ignore")
BRACKET = re.compile(r"\s*\[([^\[\]]*)\]")


@dataclass(kw_only=True)
class Suppressions:
    """A file's line→codes suppression map, plus its invalid directives."""

    by_line: dict[int, frozenset[str]]
    errors: list[DirectiveError]

    def suppresses(self, violation: Violation) -> bool:
        """Report whether a directive on the violation's line silences its code."""
        codes = self.by_line.get(violation.location.line or 0, frozenset())
        return violation.rule.code in codes


def extract(text: str, *, path: Path, known_codes: frozenset[str]) -> Suppressions:
    """Scan the file's COMMENT tokens for directives; build the map and errors."""
    by_line: dict[int, set[str]] = {}
    errors: list[DirectiveError] = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        line, comment_col = token.start
        for marker in MARKER.finditer(token.string):
            # `tokenize` reports a 0-based column; `Location.col` is 1-based.
            location = Location(
                path=path, line=line, col=comment_col + marker.start() + 1
            )
            bracket = BRACKET.match(token.string, marker.end())
            codes = [code.strip() for code in bracket.group(1).split(",")] if bracket else []
            for code in codes:
                if code in known_codes:
                    by_line.setdefault(line, set()).add(code)
                else:
                    errors.append(
                        DirectiveError(
                            location=location, message=f"unknown code {code}"
                        )
                    )
    return Suppressions(
        by_line={line: frozenset(codes) for line, codes in by_line.items()},
        errors=errors,
    )
