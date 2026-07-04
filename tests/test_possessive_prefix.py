"""GAC011 possessive-`my`: which name forms the text-scope rule flags.

Cases run through a `.md` file so text scope is exercised directly, with no
Python parse-validity concern.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import main

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def write_doc(root: Path, content: str) -> None:
    """Lay down a minimal fixture project with a single `doc.md`."""
    (root / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n', encoding="utf-8"
    )
    (root / "doc.md").write_text(content, encoding="utf-8")


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
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Each possessive-`my` form is flagged as GAC011 (exit 1)."""
    write_doc(tmp_path, f"{snippet}\n")
    monkeypatch.chdir(tmp_path)

    code = main(["doc.md"])

    out = capsys.readouterr().out
    assert "GAC011" in out
    assert code == 1


@pytest.mark.parametrize("snippet", IGNORED)
def test_ignored_forms(
    snippet: str,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Non-possessive text is left alone (no GAC011, exit 0)."""
    write_doc(tmp_path, f"{snippet}\n")
    monkeypatch.chdir(tmp_path)

    code = main(["doc.md"])

    captured = capsys.readouterr()
    assert "GAC011" not in captured.out
    assert code == 0
