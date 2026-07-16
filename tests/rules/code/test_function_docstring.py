"""GAC010 function-docstring: every function/method/nested function has a docstring.

Unlike ruff's `D` rules, this covers `_`-prefixed and nested functions too. A
documented function is left alone; a class or module without a docstring is not
flagged (the rule is functions-only). These cases run end-to-end through a `.py`
file.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun


FLAGGED = {
    "module-function": "def f():\n    pass\n",
    "method": "class C:\n    def m(self):\n        pass\n",
    "nested-function": (
        'def outer():\n    """Outer doc."""\n    def inner():\n        return 1\n'
    ),
}

IGNORED = {
    "documented-module-function": 'def f():\n    """Doc."""\n',
    "documented-method": 'class C:\n    def m(self):\n        """Doc."""\n',
    "documented-nested-function": (
        "def outer():\n"
        '    """Outer doc."""\n'
        "    def inner():\n"
        '        """Inner doc."""\n'
        "        return 1\n"
    ),
    "class-without-docstring": 'class C:\n    def m(self):\n        """Doc."""\n',
    "module-without-docstring": "x = 1\n",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_functions(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A function/method/nested function lacking a docstring is flagged GAC010."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC010" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_functions(
    *,
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A documented function, or a class/module without one, is left alone."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC010" not in run.codes


def test_locates_nested_function_at_its_indented_column(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A nested function's GAC010 locates at the indented `def` — column included."""
    project(
        {
            "src/mod.py": (
                "def outer():\n"
                '    """Outer doc."""\n'
                "    def inner():\n"
                "        return 1\n"
            )
        }
    )

    run = lint(["src"])

    assert run.at("src/mod.py", line=3, col=5) == ["GAC010"]
