"""GAC006 self-return: return `Self`, not a string forward-ref to the class.

A `"ClassName"` string forward-ref naming the enclosing class silently lies
after a rename and does not follow into subclasses. A `-> Self`, a forward-ref to
a *different* name, or a module-level function are left alone. These cases run
end-to-end through a `.py` file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


SELF_FORWARD_REF = 'class W:\n    def clone(self) -> "W":\n        return self\n'

IGNORED = {
    "returns-self": (
        "from typing import Self\n"
        "class W:\n"
        "    def clone(self) -> Self:\n"
        "        return self\n"
    ),
    "forward-ref-different-name": (
        'class W:\n    def clone(self) -> "Other":\n        return self\n'
    ),
    "module-level-self-string": 'def make() -> "make":\n    return make\n',
}


def test_flags_self_forward_ref(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A method returning a string forward-ref to its own class is flagged GAC006."""
    project({"src/mod.py": SELF_FORWARD_REF})

    run = lint(["src"])

    assert "GAC006" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_returns(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`Self`, a different forward-ref, or a module function is left alone."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC006" not in run.codes


def test_locates_at_the_return_annotation(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the return annotation, not the `def`."""
    project({"src/mod.py": SELF_FORWARD_REF})

    run = lint(["src"])

    assert run.at("src/mod.py", line=2, col=24) == ["GAC006"]
