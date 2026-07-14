"""The rendered explanation block: exact layout, gutter, and continuation.

`render_explanation` lays a rule's explanation out with a right-aligned label in
a seven-column gutter, two spaces, then the text; continuation lines align under
the text, and an author's own indentation (a code example inside `fix`) is kept.
The block is asserted as an exact string against a fixture rule, so the geometry
is pinned independently of any real rule's prose wrapping.
"""

from pathlib import Path

from garuff.output import render_appendix, render_explanation
from garuff.rule import Explanation, Rule
from garuff.rules.code.future_import import FUTURE_ANNOTATIONS_IMPORT
from garuff.rules.code.positional_args import POSITIONAL_ARGS
from garuff.schemas import Location, Violation


def violation(rule: Rule, *, line: int) -> Violation:
    """Build a throwaway violation of `rule` at a fixed file, for appendix assembly."""
    return Violation(rule=rule, location=Location(path=Path("m.py"), line=line, col=1))


def header_codes(appendix: str) -> list[str]:
    """Return the codes appearing as block headers (a `  CODE  ` line), in order."""
    return [
        line.split()[0]
        for line in appendix.splitlines()
        if line.startswith("  ") and line[2:3].isalpha()
    ]


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


def test_appendix_is_empty_without_violations() -> None:
    """No violations means no appendix — the CLI then writes nothing."""
    assert render_appendix(violations=[]) == ""


def test_appendix_has_one_code_sorted_block_per_distinct_rule() -> None:
    """Distinct fired rules each get one block, code-sorted regardless of order."""
    violations = [
        violation(POSITIONAL_ARGS, line=9),
        violation(FUTURE_ANNOTATIONS_IMPORT, line=2),
        violation(POSITIONAL_ARGS, line=5),
    ]

    appendix = render_appendix(violations=violations)

    assert header_codes(appendix) == ["GAC001", "GAC008"]


def test_appendix_dedupes_many_hits_of_one_rule_to_one_block() -> None:
    """Forty violations of one rule produce exactly one explanation block."""
    violations = [violation(FUTURE_ANNOTATIONS_IMPORT, line=n) for n in range(40)]

    appendix = render_appendix(violations=violations)

    assert header_codes(appendix) == ["GAC001"]


def test_appendix_indents_every_non_blank_line_by_two_spaces() -> None:
    """The layout invariant: no appendix line sits at column 0 unless blank."""
    appendix = render_appendix(violations=[violation(POSITIONAL_ARGS, line=1)])

    for line in appendix.splitlines():
        assert line == "" or line.startswith("  "), repr(line)
