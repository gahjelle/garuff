"""The rendered explanation block: exact layout, gutter, and continuation.

`render_explanation` lays a rule's explanation out with a right-aligned label in
a seven-column gutter, two spaces, then the text; continuation lines align under
the text, and an author's own indentation (a code example inside `fix`) is kept.
The block is asserted as an exact string against a fixture rule, so the geometry
is pinned independently of any real rule's prose wrapping.
"""

from garuff.output import render_explanation
from garuff.rule import Explanation


def fixture_explanation() -> Explanation:
    """Build a small explanation with a multi-line rationale and an indented fix."""
    return Explanation(
        code="GAX001",
        summary="a short summary",
        rationale="first line\nsecond line",
        fix="do this:\n    example()",
    )


def test_render_explanation_without_a_note() -> None:
    """Header, why, and fix render with the gutter geometry and no note line."""
    block = render_explanation(fixture_explanation())

    assert block == (
        "GAX001  a short summary\n"
        "    why  first line\n"
        "         second line\n"
        "    fix  do this:\n"
        "             example()"
    )


def test_render_explanation_with_a_note() -> None:
    """A note is a fourth labelled line, right-aligned in the same gutter."""
    block = render_explanation(
        fixture_explanation(), note="ignored in this project's configuration"
    )

    assert block == (
        "GAX001  a short summary\n"
        "    why  first line\n"
        "         second line\n"
        "    fix  do this:\n"
        "             example()\n"
        "   note  ignored in this project's configuration"
    )
