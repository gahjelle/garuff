"""End-to-end `garuff check --fix` behaviour, observed through the CLI.

These drive `main(["check", "--fix", ...])` over throwaway fixture projects and
assert on both what the agent sees (the parsed findings, the summary, the exit
code) and what lands on disk (the rewritten file text). A fixer is observable
only here — through the file it rewrites and the remainder it leaves to report —
so every fixer earns its keep with a case in this module.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import branding, main
from tests.lintrun import LintRun

if TYPE_CHECKING:
    from collections.abc import Callable

FUTURE_IMPORT = "from __future__ import annotations\n"  # trips GAC001
DOUBLE_DOC = 'def f():\n    """Return the ``value``."""\n    return 1\n'  # GAC004
DOUBLE_DOC_FIXED = 'def f():\n    """Return the `value`."""\n    return 1\n'
TWO_POSITIONAL = (  # trips GAC008 only (documented), not fixable
    'def g(a, b):\n    """Return the first argument."""\n    return a\n'
)


@pytest.fixture
def garuff(*, capsys: pytest.CaptureFixture[str]) -> Callable[[list[str]], LintRun]:
    """Run `garuff` with arbitrary argv and parse the outcome as a LintRun."""

    def run(argv: list[str]) -> LintRun:
        """Invoke `garuff` with `argv` and capture the run as a LintRun."""
        exit_code = main(argv)
        captured = capsys.readouterr()
        return LintRun(exit_code=exit_code, stdout=captured.out, stderr=captured.err)

    return run


@pytest.fixture
def fix(
    *,
    garuff: Callable[[list[str]], LintRun],
) -> Callable[[list[str]], LintRun]:
    """Run `garuff check --fix` over `paths` and parse the outcome, like `lint`."""

    def run(paths: list[str]) -> LintRun:
        """Invoke `garuff check --fix` over `paths` and capture it as a LintRun."""
        return garuff(["check", "--fix", *paths])

    return run


def test_fix_deletes_future_import_and_reports_zero(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """GAC001: `--fix` deletes the future-import line, rewrites the file, exit 0."""
    root = project({"mod.py": FUTURE_IMPORT + "x = 1\n"})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == "x = 1\n"
    assert run.codes == []
    assert run.exit_code == 0
    assert "1 fix," in run.stderr


def test_fix_collapses_double_backticks_in_docstring(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """GAC004: `--fix` collapses a double backtick in a docstring to a single one."""
    source = 'def f():\n    """Return the ``value``."""\n    return 1\n'
    root = project({"mod.py": source})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(
        encoding="utf-8"
    ) == 'def f():\n    """Return the `value`."""\n    return 1\n'
    assert run.at("mod.py", line=2, col=5) == []
    assert run.exit_code == 0


PROTOCOL_WITH_DOC = (
    "from typing import Protocol\n\n\n"
    "class Reader(Protocol):\n"
    "    def read(self) -> bytes:\n"
    '        """Return the payload."""\n'
    "        ...\n"
)


def test_fix_deletes_redundant_ellipsis_when_docstring_remains(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """GAC003: a documented Protocol method's `...` line is deleted, leaving the doc."""
    root = project({"mod.py": PROTOCOL_WITH_DOC})

    run = fix(["mod.py"])

    result = (root / "mod.py").read_text(encoding="utf-8")
    assert "..." not in result
    assert '"""Return the payload."""' in result
    assert "GAC003" not in run.codes
    assert run.exit_code == 0


PROTOCOL_NO_DOC = (
    "from typing import Protocol\n\n\n"
    "class Reader(Protocol):\n"
    "    def read(self) -> bytes:\n"
    "        ...\n"
)


def test_fix_leaves_ellipsis_when_it_is_the_sole_body_line(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """GAC003 guard: an undocumented `...` is not deleted (would be a SyntaxError).

    The occurrence survives into the re-check and is still reported (alongside
    GAC010, which nudges the agent to add a docstring first), and the file still
    parses.
    """
    root = project({"mod.py": PROTOCOL_NO_DOC})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == PROTOCOL_NO_DOC
    assert "GAC003" in run.codes
    assert "GAC010" in run.codes
    assert run.exit_code == 1


def test_fix_leaves_a_non_fixable_rule_untouched(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A rule with no fixer (GAC008) is neither changed nor silenced by `--fix`."""
    root = project({"mod.py": TWO_POSITIONAL})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == TWO_POSITIONAL
    assert "GAC008" in run.codes
    assert run.exit_code == 1


def test_fix_applies_multiple_fixers_in_one_write(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A future import and a double-backtick docstring are both fixed in one pass."""
    root = project({"mod.py": FUTURE_IMPORT + "\n\n" + DOUBLE_DOC})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == "\n\n" + DOUBLE_DOC_FIXED
    assert run.codes == []
    assert "2 fixes," in run.stderr
    assert run.exit_code == 0


def test_fix_respects_inline_suppression(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """An inline-suppressed occurrence is neither fixed nor reported."""
    source = "from __future__ import annotations  # garuff: ignore[GAC001]\nx = 1\n"
    root = project({"mod.py": source})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == source
    assert run.codes == []
    assert "0 fixes," in run.stderr


def test_fix_respects_per_file_ignores(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A per-file-ignored code is not fixed in the matching file, but is elsewhere."""
    root = project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            f"[{branding.CONFIG_TABLE}.per-file-ignores]\n"
            '"pkg/skip.py" = ["GAC004"]\n',
            "pkg/skip.py": DOUBLE_DOC,
            "pkg/other.py": DOUBLE_DOC,
        }
    )

    fix(["pkg"])

    assert (root / "pkg/skip.py").read_text(encoding="utf-8") == DOUBLE_DOC
    assert (root / "pkg/other.py").read_text(encoding="utf-8") == DOUBLE_DOC_FIXED


def test_fix_respects_global_ignore(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A globally-ignored code is neither fixed nor reported."""
    root = project(
        {
            "pyproject.toml": '[project]\nname = "sample"\n'
            f'[{branding.CONFIG_TABLE}]\nignore = ["GAC001"]\n',
            "mod.py": FUTURE_IMPORT + "x = 1\n",
        }
    )

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == FUTURE_IMPORT + "x = 1\n"
    assert run.codes == []


def test_fix_is_idempotent(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A second `--fix` run applies zero fixes and leaves the file byte-identical."""
    root = project({"mod.py": FUTURE_IMPORT + DOUBLE_DOC})

    fix(["mod.py"])
    after_first = (root / "mod.py").read_text(encoding="utf-8")
    second = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == after_first
    assert "0 fixes," in second.stderr
    assert second.exit_code == 0


def test_fix_reports_only_the_unfixable_remainder(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """A fixable + unfixable pair leaves only the unfixable in findings + appendix."""
    root = project({"mod.py": FUTURE_IMPORT + "\n\n" + TWO_POSITIONAL})

    run = fix(["mod.py"])

    assert "GAC001" not in run.codes
    assert run.codes == ["GAC008"]
    assert run.codes_explained == ["GAC008"]
    assert (root / "mod.py").read_text(encoding="utf-8") == "\n\n" + TWO_POSITIONAL


def test_fix_preserves_untouched_bytes(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """Deleting one line leaves every other byte — including a missing final newline."""
    source = "x = 1\n" + FUTURE_IMPORT + "y = 2"  # note: no trailing newline
    root = project({"mod.py": source})

    fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == "x = 1\ny = 2"


def test_normal_check_never_writes_and_omits_the_fixes_clause(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`garuff check` without `--fix` leaves files alone and shows no fixes clause."""
    source = FUTURE_IMPORT + "x = 1\n"
    root = project({"mod.py": source})

    run = lint(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == source
    assert "GAC001" in run.codes
    assert "fix" not in run.stderr


def test_fix_skips_an_unparseable_file(
    *,
    project: Callable[[dict[str, str]], Path],
    fix: Callable[[list[str]], LintRun],
) -> None:
    """An unparseable `.py` is not written under `--fix`; it is a parse failure."""
    source = "def broken(\n"
    root = project({"mod.py": source})

    run = fix(["mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == source
    assert "could not parse" in run.stderr
    assert run.exit_code == 1


def test_quiet_fix_drops_summary_but_still_fixes_and_reports(
    *,
    project: Callable[[dict[str, str]], Path],
    garuff: Callable[[list[str]], LintRun],
) -> None:
    """`--fix -q` applies fixes and prints remaining findings, but no summary."""
    root = project({"mod.py": FUTURE_IMPORT + "\n\n" + TWO_POSITIONAL})

    run = garuff(["check", "--fix", "-q", "mod.py"])

    assert (root / "mod.py").read_text(encoding="utf-8") == "\n\n" + TWO_POSITIONAL
    assert run.codes == ["GAC008"]
    assert "linted" not in run.stderr  # the summary (with its fixes clause) is gone
