"""Strict config validation and rule resolution, observed through the CLI.

garuff reads and validates the tool's config table before it lints. Every
outcome here is asserted the way a user sees it — the exit code and the messages
or violations `main()` emits — never by poking at `config.load` internals: a bad
config aborts with exit 2 and names the offending key or code, while a valid
`ignore`, option override, or `per-file-ignores` glob changes which violations
appear. Fixtures are throwaway projects under `tmp_path` (see conftest).
"""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import branding

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.lintrun import LintRun

FUTURE_IMPORT = "from __future__ import annotations\n"  # trips GAC001
TWO_POSITIONAL = 'def f(a, b):\n    """Doc."""\n    return a\n'  # trips GAC008


def pyproject(body: str) -> str:
    """Return `pyproject.toml` text carrying the given config-table body."""
    return f'[project]\nname = "sample"\n{body}'


def test_rules_are_active_without_a_config_table(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """With no config table, every rule stays on — GAC001 still fires."""
    project({"src/mod.py": FUTURE_IMPORT})

    run = lint(["src"])

    assert run.exit_code == 1
    assert run.at("src/mod.py", line=1, col=1) == ["GAC001"]


def test_ignore_drops_the_named_rule(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A code in `ignore` no longer fires — the tripping file comes back clean."""
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}]\nignore = ["GAC001"]\n'
            ),
            "src/mod.py": FUTURE_IMPORT,
        }
    )

    run = lint(["src"])

    assert run.exit_code == 0
    assert "GAC001" not in run.codes


def test_ignore_drops_a_project_scope_rule(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`ignore` is the only lever for a project-scope rule (GAA), and it works."""
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}]\nignore = ["GAA001"]\n'
            ),
            "docs/adr/0001-first.md": "First ADR.\n",
            "docs/adr/0001-again.md": "Another ADR.\n",
        }
    )

    run = lint(["docs"])

    assert run.exit_code == 0
    assert "GAA001" not in run.codes


def test_unknown_ignore_code_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """An `ignore` code no rule provides is a hard config error, not a warning."""
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}]\nignore = ["GAC999"]\n'
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "GAC999" in run.stderr


def test_dead_glob_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `per-file-ignores` glob that matches no project file is a config error."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.per-file-ignores]\n"
                '"nowhere/**" = ["GAC001"]\n'
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "nowhere/" in run.stderr


def test_glob_is_live_against_the_whole_project_not_the_run(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `tests/**` glob stays live even when only `src/` is linted (ADR-0008).

    Judged against the run's files a `tests/**` glob would match nothing when
    linting `src/` and abort with exit 2; judged against the whole project it is
    live, so the run proceeds and flags `src/` normally.
    """
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}.per-file-ignores]\n"tests/**" = ["GAC001"]\n'
            ),
            "src/mod.py": FUTURE_IMPORT,
            "tests/test_mod.py": FUTURE_IMPORT,
        }
    )

    run = lint(["src"])

    assert run.exit_code == 1
    assert run.at("src/mod.py", line=1, col=1) == ["GAC001"]


def test_unknown_top_level_key_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A key outside {ignore, per-file-ignores, rules} is a config error."""
    project(
        {
            "pyproject.toml": pyproject(f"[{branding.CONFIG_TABLE}]\nfoo = 1\n"),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "foo" in run.stderr


def test_options_for_an_optionless_rule_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `rules.<CODE>` table for a rule with no options is a config error."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.rules.GAC001]\nfoo = 1\n"
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "GAC001" in run.stderr


def test_unknown_option_key_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """An option key the rule's schema does not declare is a config error."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.rules.GAC008]\nnonsense = 1\n"
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "nonsense" in run.stderr


def test_wrong_option_type_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """An option value of the wrong type is a config error, not a coercion."""
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}.rules.GAC008]\nmax-positional-args = "two"\n'
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "max-positional-args" in run.stderr


def test_unknown_rule_code_in_options_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `rules.<CODE>` table for an unknown code is a config error."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.rules.GAC999]\nmax-positional-args = 2\n"
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "GAC999" in run.stderr


def test_option_override_changes_what_is_flagged(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """`max-positional-args = 3` permits three positional params but not four."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.rules.GAC008]\nmax-positional-args = 3\n"
            ),
            "src/three.py": 'def f(a, b, c):\n    """Doc."""\n    return a\n',
            "src/four.py": 'def g(a, b, c, d):\n    """Doc."""\n    return a\n',
        }
    )

    run = lint(["src"])

    assert run.at("src/three.py", line=1, col=1) == []
    assert run.at("src/four.py", line=1, col=1) == ["GAC008"]


def test_per_file_ignores_silence_the_listed_codes(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `tests/**` entry listing two codes silences both under tests/."""
    project(
        {
            "pyproject.toml": pyproject(
                f"[{branding.CONFIG_TABLE}.per-file-ignores]\n"
                '"tests/**" = ["GAC001", "GAC008"]\n'
            ),
            "tests/test_a.py": FUTURE_IMPORT + "\n" + TWO_POSITIONAL,
        }
    )

    run = lint(["tests"])

    assert run.exit_code == 0
    assert run.codes == []


def test_unknown_per_file_ignore_code_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """An unknown code in a `per-file-ignores` value is a config error."""
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}.per-file-ignores]\n"tests/**" = ["GAC999"]\n'
            ),
            "tests/test_a.py": "x = 1\n",
        }
    )

    run = lint(["tests"])

    assert run.exit_code == 2
    assert "GAC999" in run.stderr


def test_project_scope_code_in_per_file_ignores_aborts_with_exit_two(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A project-scope rule can't be silenced per-file — that's a config error.

    Per-file-ignores act on source/text rules; a project-scope rule (GAA) sees
    the whole tree at once, so listing it here would silently no-op. Strict
    config rejects it and points the user at `ignore`.
    """
    project(
        {
            "pyproject.toml": pyproject(
                f'[{branding.CONFIG_TABLE}.per-file-ignores]\n"tests/**" = ["GAA001"]\n'
            ),
            "tests/test_a.py": "x = 1\n",
        }
    )

    run = lint(["tests"])

    assert run.exit_code == 2
    assert "GAA001" in run.stderr
    assert "ignore" in run.stderr
