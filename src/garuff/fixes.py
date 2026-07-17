"""Apply layer — turn a fixer's located Edits into rewritten file text.

Behaviour that transforms text, kept out of `schemas.py` (passive value types,
ADR-0004). A fixer yields `Edit`s against AST node positions; the helpers here
convert those 1-based/0-based coordinates into absolute character offsets, and
`apply_edits` splices the guard-passing, non-overlapping ones into the text —
high-offset-first so earlier offsets never shift. See ADR-0017.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast

    from garuff.schemas import Edit


def line_starts(text: str) -> list[int]:
    """Absolute offset at which each 1-based line begins.

    `line_starts(text)[n - 1]` is the offset of line `n`'s first character;
    `line_starts(text)[n]` is the offset just past line `n`'s newline, i.e. the
    start of line `n + 1`.
    """
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def offset_at(*, line: int, col: int, starts: list[int]) -> int:
    """Convert a 1-based (line, col) — Location coordinates — to a char offset.

    `starts` is `line_starts(text)`; it already encodes every line's origin, so
    the text itself is not needed here.
    """
    return starts[line - 1] + (col - 1)


def node_span(node: ast.stmt | ast.expr, *, starts: list[int]) -> tuple[int, int]:
    """Return the half-open char range a node occupies, from its AST position.

    Uses the node's `lineno`/`col_offset` start and `end_lineno`/`end_col_offset`
    end (AST columns are 0-based, so `offset_at`'s 1-based col is the AST col + 1).
    The end positions are `int | None` in the typeshed but always present on a
    parsed node, so they fall back to the start on the impossible `None`.
    """
    end_line = node.end_lineno or node.lineno
    end_col = (
        node.end_col_offset if node.end_col_offset is not None else node.col_offset
    )
    start = offset_at(line=node.lineno, col=node.col_offset + 1, starts=starts)
    end = offset_at(line=end_line, col=end_col + 1, starts=starts)
    return start, end


def whole_lines_span(
    node: ast.stmt | ast.expr, *, text: str, starts: list[int]
) -> tuple[int, int]:
    """Return the char range covering every physical line a statement occupies.

    From the start of the node's first line to the start of the line after its
    last — so deleting `[start, end)` removes the whole statement including its
    trailing newline. Clamped to the text length for a final line with no newline.
    """
    end_line = node.end_lineno or node.lineno
    start = starts[node.lineno - 1]
    end = starts[end_line] if end_line < len(starts) else len(text)
    return start, end


def apply_edits(text: str, *, edits: list[Edit]) -> tuple[str, list[Edit]]:
    """Apply non-overlapping, guard-passing edits high-offset-first.

    Returns the new text and the edits actually applied. An edit is skipped (and
    omitted from the applied list) when its `[start, end)` overlaps an
    already-accepted edit, or when `text[start:end] != original`. Acceptance is
    decided in location order; the accepted set is then spliced high-offset-first
    so no earlier offset is invalidated by a later splice.
    """
    accepted: list[Edit] = []
    for candidate in edits:
        if text[candidate.start : candidate.end] != candidate.original:
            continue
        if any(
            candidate.start < other.end and other.start < candidate.end
            for other in accepted
        ):
            continue
        accepted.append(candidate)
    result = text
    for edit in sorted(accepted, key=lambda item: item.start, reverse=True):
        result = result[: edit.start] + edit.replacement + result[edit.end :]
    return result, accepted
