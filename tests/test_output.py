"""The rendered explanation block: exact layout, gutter, and continuation.

`render_explanation` lays a rule's explanation out with a right-aligned label in
a seven-column gutter, two spaces, then the text; continuation lines align under
the text, and an author's own indentation (a code example inside `fix`) is kept.
The block is asserted as an exact string against a fixture explanation, so the
geometry is pinned independently of any real rule's prose wrapping — a pure
render seam the CLI convention explicitly allows (see `docs/agents/testing.md`).
Which rules appear (dedupe, code-sort, notes) is `explain`'s job and is asserted
end-to-end in `test_appendix.py` / `test_rule_command.py`, not here.
"""

from garuff.explain import ExplainedRule
from garuff.output import (
    Verbosity,
    render_appendix,
    render_explanation,
    render_explanations,
    render_summary,
)
from garuff.rule import Explanation


def test_verbosity_quiet_ranks_below_default() -> None:
    """The scale is ordered low-to-high, so quiet compares less than default.

    Output gates read as thresholds (`verbosity >= Verbosity.DEFAULT`); this
    ordering is what makes reserving `SILENT` below and `VERBOSE` above a
    non-breaking extension (ADR-0016, #42).
    """
    assert Verbosity.QUIET < Verbosity.DEFAULT


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
        "   why  first line\n"
        "        second line\n"
        "   fix  do this:\n"
        "            example()"
    )


def test_render_explanation_with_a_note() -> None:
    """A note is a fourth labelled line, right-aligned in the same gutter."""
    block = render_explanation(
        fixture_explanation(), note="ignored in this project's configuration"
    )

    assert block == (
        "GAX001  a short summary\n"
        "   why  first line\n"
        "        second line\n"
        "   fix  do this:\n"
        "            example()\n"
        "  note  ignored in this project's configuration"
    )


def test_render_explanations_joins_blocks_with_one_blank_line() -> None:
    """The `rule` render separates each selected block by exactly one blank line."""
    rules = [
        ExplainedRule(explanation=fixture_explanation()),
        ExplainedRule(explanation=fixture_explanation(), note="a note"),
    ]

    rendered = render_explanations(rules)

    assert rendered.count("\n\n") == 1
    assert rendered.endswith("  note  a note")


def test_appendix_is_empty_without_rules() -> None:
    """No selected rules means no appendix — the CLI then writes nothing."""
    assert render_appendix([]) == ""


def test_appendix_indents_every_non_blank_line_by_two_spaces() -> None:
    """The layout invariant: no appendix line sits at column 0 unless blank."""
    appendix = render_appendix([ExplainedRule(explanation=fixture_explanation())])

    for line in appendix.splitlines():
        assert line == "" or line.startswith("  "), repr(line)


def summary(*, violations: int, fixes: int | None) -> str:
    """Render a one-`.py`-file summary with the given violation and fixes counts."""
    return render_summary(
        linted_by_suffix={".py": 1},
        skipped=0,
        violations=violations,
        fixes=fixes,
    )


def test_summary_omits_the_fixes_clause_on_a_normal_run() -> None:
    """`fixes=None` (no `--fix`) prints no fixes clause — no `0 fixes` noise."""
    assert summary(violations=2, fixes=None) == "1 .py file linted: 2 violations"


def test_summary_shows_fixes_clause_before_violations_under_fix() -> None:
    """A `--fix` run inserts the fixes count before the violations count."""
    assert summary(violations=2, fixes=4) == "1 .py file linted: 4 fixes, 2 violations"


def test_summary_fixes_clause_uses_irregular_singular() -> None:
    """One fix reads `1 fix`, not `1 fixs`; zero and plural read `fixes`."""
    assert "1 fix, " in summary(violations=0, fixes=1)
    assert "0 fixes, " in summary(violations=0, fixes=0)
