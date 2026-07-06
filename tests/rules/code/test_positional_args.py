"""GAC008 positional-args: which callables trip the max-1-positional guardrail.

The rule counts a function's positional parameters (posonly + normal), ignoring
keyword-only params, `*args`, and `**kwargs`. A method's first positional
(`self`/`cls`) is exempt by structural `ClassDef` detection — unless the method
is a `@staticmethod`. Lambdas are not checked. These cases run end-to-end through
a `.py` file so registration and the default option (max 1) are exercised too.
"""

from typing import TYPE_CHECKING

import pytest

from garuff import branding

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun


FLAGGED = {
    "two-plain-params": "def f(a, b):\n    pass\n",
    "two-posonly-params": "def f(a, b, /):\n    pass\n",
    "method-self-plus-two": "class C:\n    def m(self, a, b):\n        pass\n",
    "staticmethod-two": (
        "class C:\n    @staticmethod\n    def m(a, b):\n        pass\n"
    ),
    "nested-two-params": (
        "def outer():\n    def inner(a, b):\n        return a\n    return inner\n"
    ),
}

IGNORED = {
    "one-plain-param": "def f(a):\n    pass\n",
    "method-self-only": "class C:\n    def m(self):\n        pass\n",
    "method-self-plus-one": "class C:\n    def m(self, a):\n        pass\n",
    "classmethod-cls-plus-one": (
        "class C:\n    @classmethod\n    def m(cls, a):\n        pass\n"
    ),
    "staticmethod-one": ("class C:\n    @staticmethod\n    def m(a):\n        pass\n"),
    "keyword-only-ignored": "def f(a, *, b, c):\n    pass\n",
    "varargs-and-kwargs-ignored": "def f(a, *args, **kwargs):\n    pass\n",
    "lambda-not-checked": "f = lambda a, b: a  # noqa: E731\n",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_flagged_functions(
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A function with more than one positional parameter is flagged GAC008."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC008" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("source", IGNORED.values(), ids=IGNORED.keys())
def test_ignored_functions(
    source: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A function within the positional-arg limit is left alone (no GAC008)."""
    project({"src/mod.py": source})

    run = lint(["src"])

    assert "GAC008" not in run.codes


def test_locates_at_the_def_line(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The violation locates to the `def` line and column, not a parameter."""
    project({"src/mod.py": "def f(a, b):\n    pass\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", 1, 1) == ["GAC008"]


def test_max_positional_args_option_raises_the_ceiling(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`max-positional-args = 2` permits two positional params but not three."""
    project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            f"[{branding.CONFIG_TABLE}.rules.GAC008]\nmax-positional-args = 2\n",
            "src/two.py": "def f(a, b):\n    pass\n",
            "src/three.py": "def g(a, b, c):\n    pass\n",
        }
    )

    run = lint(["src"])

    assert run.at("src/two.py", 1, 1) == []
    assert run.at("src/three.py", 1, 1) == ["GAC008"]
