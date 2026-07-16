"""GAC003 redundant-ellipsis: a `Protocol` method's `...` body is redundant.

Scoped to `Protocol` methods: once the method carries a docstring, its `...`
placeholder is dead weight. A `...` in a non-Protocol class, or a method with no
`...`, is left alone. These cases run end-to-end through a `.py` file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


PROTOCOL_WITH_ELLIPSIS = (
    "from typing import Protocol\n"
    "class R(Protocol):\n"
    "    def read(self) -> bytes:\n"
    '        """doc"""\n'
    "        ...\n"
)

FLAGGED = {
    "protocol-method-ellipsis": PROTOCOL_WITH_ELLIPSIS,
    "dotted-protocol-base": (
        "import typing\n"
        "class R(typing.Protocol):\n"
        "    def read(self) -> bytes:\n"
        '        """doc"""\n'
        "        ...\n"
    ),
}

IGNORED = {
    "protocol-method-no-ellipsis": (
        "from typing import Protocol\n"
        "class R(Protocol):\n"
        "    def read(self) -> bytes:\n"
        '        """doc"""\n'
        "        return b''\n"
    ),
    "ellipsis-in-non-protocol-class": (
        "class R:\n    def read(self) -> bytes:\n        ...\n"
    ),
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_ellipsis(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `...` statement in a Protocol method is flagged GAC003."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC003" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_ellipsis(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A method with no `...`, or a `...` outside a Protocol, is left alone."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC003" not in run.codes


def test_locates_at_the_ellipsis_line(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the `...` statement, not the method def."""
    project({"src/mod.py": PROTOCOL_WITH_ELLIPSIS})

    run = lint(["src"])

    assert run.at("src/mod.py", line=5, col=9) == ["GAC003"]
