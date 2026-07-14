"""GAC011 — no possessive `my` prefix.

A name that opens with a first-person possessive is often used in examples, but
actually provides a bad example to  users on how variables, functions, and
classes should be named. These are never "mine", and examples should also use
proper, descriptive naming. This is a text-scope rule: it scans the raw file, so
it fires in Markdown as well as Python.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import TextRule
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator

# Match a first-person possessive opening an identifier segment. The snake and
# kebab forms (an underscore or hyphen separator) are case-insensitive; the
# PascalCase form is case-sensitive and needs an uppercase letter after the
# prefix, so a lowercase camelCase spelling is deliberately left alone. The
# lookbehind lets a leading underscore or separator through while rejecting
# mid-word matches such as the tail of an unrelated longer word.
POSSESSIVE_PATTERN = re.compile(r"(?<![A-Za-z0-9])([Mm][Yy][_-]|My[A-Z])")


class PossessivePrefix(TextRule):
    """Flag a possessive `my` prefix anywhere in a file's raw text."""

    def check(self, text: str, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each possessive `my` prefix in the text."""
        for match in POSSESSIVE_PATTERN.finditer(text):
            yield Violation(
                rule=self,
                location=Location.from_offset(
                    text=text, offset=match.start(), path=path
                ),
            )


POSSESSIVE_PREFIX = PossessivePrefix(
    code="GAC011",
    summary="no possessive `my` prefix",
    rationale="""
        A name opening with a first-person possessive — `my_config`, `MyClass`,
        `my-thing` — reads as throwaway example code. Nothing in a codebase is
        "mine", and examples are the naming other code copies, so the name must
        describe what the thing *is*.
    """,
    fix="""
        Rename to something descriptive:
            my_config = load()   # before
            settings = load()    # after
    """,
)
