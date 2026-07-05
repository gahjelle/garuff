"""GAC011 possessive-`my`: which name forms the rule flags, in Python and text.

Form cases run through a `.md` file so text scope is exercised directly, with
no Python parse-validity concern; two end-to-end cases confirm the rule fires in
both a `.py` source and a Markdown file.
"""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tests.lintrun import LintRun


FLAGGED = [
    "my_thing",
    "my-thing",
    "MyClass",
    "MY_CONST",
    "MY-CONST",
    "_my_thing",
    "foo_my_thing",
]

IGNORED = [
    "army_base",
    "enemy_list",
    "myThing",  # camelCase (lowercase m) is deliberately uncovered
    "my thing",  # prose 'my' with a space, not a possessive prefix
    "summary",
]


@pytest.mark.parametrize("snippet", FLAGGED)
def test_flagged_forms(
    snippet: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Each possessive-`my` form is flagged as GAC011 (exit 1)."""
    project({"doc.md": f"{snippet}\n"})

    run = lint(["doc.md"])

    assert "GAC011" in run.codes
    assert run.exit_code == 1


@pytest.mark.parametrize("snippet", IGNORED)
def test_ignored_forms(
    snippet: str,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """Non-possessive text is left alone (no GAC011, exit 0)."""
    project({"doc.md": f"{snippet}\n"})

    run = lint(["doc.md"])

    assert "GAC011" not in run.codes
    assert run.exit_code == 0


def test_flags_possessive_prefix_in_python(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A possessive `my` prefix in a .py source is flagged as GAC011."""
    project({"src/mod.py": "my_thing = 1\n"})

    run = lint(["src"])

    assert run.at("src/mod.py", 1, 1) == ["GAC011"]
    assert run.exit_code == 1


def test_flags_possessive_prefix_in_markdown(
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A possessive `my` prefix in a Markdown file is flagged as GAC011."""
    project({"docs/guide.md": "See the `MyClass` helper.\n"})

    run = lint(["docs/guide.md"])

    assert run.at("docs/guide.md", 1, 10) == ["GAC011"]
    assert run.exit_code == 1
