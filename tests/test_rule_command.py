"""`garuff rule` — explain a rule on demand, reading the project's config.

`garuff rule <CODE>` renders the same baked rule the appendix would (ADR-0014),
so an explanation never disagrees with what `check` enforces. It explains a rule
that never fired, reads the project's options, still explains a globally-ignored
rule (with a note), falls back to defaults outside a project, and mirrors `ruff
rule` on an unknown code. `--all` teaches the whole ruleset at once.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from garuff import main
from tests.test_config import pyproject

if TYPE_CHECKING:
    from collections.abc import Callable


def block_headers(stdout: str) -> list[str]:
    """Return the flush-left `CODE  summary` header codes of a render, in order."""
    return [
        line.split()[0]
        for line in stdout.splitlines()
        if line and not line[0].isspace()
    ]


def test_rule_explains_a_rule_that_never_fired(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`garuff rule GAC008` renders its full block and exits 0 with no violation."""
    project({"src/mod.py": "x = 1\n"})

    code = main(["rule", "GAC008"])

    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("GAC008  keep positional parameters to at most 1\n")
    assert "why" in out
    assert "fix" in out


def test_rule_reads_the_project_option(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A configured ceiling shows in the explanation, matching what `check` enforces."""
    project(
        {
            "pyproject.toml": pyproject(
                "[tool.garuff.rules.GAC008]\nmax-positional-args = 3\n"
            ),
            "src/mod.py": "x = 1\n",
        }
    )

    code = main(["rule", "GAC008"])

    out = capsys.readouterr().out
    assert code == 0
    assert "keep positional parameters to at most 3" in out


def test_rule_outside_a_project_uses_defaults(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no pyproject up the tree, the rule prints at its default option (1)."""
    work = tmp_path / "loose"
    work.mkdir()
    monkeypatch.chdir(work)

    code = main(["rule", "GAC008"])

    out = capsys.readouterr().out
    assert code == 0
    assert "keep positional parameters to at most 1" in out


def test_rule_with_a_broken_config_exits_two(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken config aborts `rule` too — options are unknowable without it."""
    project(
        {
            "pyproject.toml": pyproject('[tool.garuff]\nignore = ["GAC999"]\n'),
            "src/mod.py": "x = 1\n",
        }
    )

    code = main(["rule", "GAC008"])

    captured = capsys.readouterr()
    assert code == 2
    assert "GAC999" in captured.err


def test_rule_explains_a_globally_ignored_rule_with_a_note(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An ignored rule still explains in full, plus a note saying it is ignored."""
    project(
        {
            "pyproject.toml": pyproject('[tool.garuff]\nignore = ["GAC008"]\n'),
            "src/mod.py": "x = 1\n",
        }
    )

    code = main(["rule", "GAC008"])

    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("GAC008  ")
    assert "ignored in this project's configuration" in out


def test_rule_unknown_code_exits_two_with_a_did_you_mean(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown code names itself and suggests a close one (like `ruff rule`)."""
    project({"src/mod.py": "x = 1\n"})

    code = main(["rule", "GAC099"])

    err = capsys.readouterr().err
    assert code == 2
    assert "GAC099" in err
    assert "did you mean" in err
    assert "GAC0" in err.split("did you mean", 1)[1]


def test_rule_all_explains_every_code_in_sorted_order(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--all` renders one block per registered rule, code-sorted."""
    project({"src/mod.py": "x = 1\n"})

    code = main(["rule", "--all"])

    out = capsys.readouterr().out
    assert code == 0
    assert block_headers(out) == [
        "GAA001",
        "GAA002",
        "GAC001",
        "GAC002",
        "GAC003",
        "GAC004",
        "GAC005",
        "GAC006",
        "GAC008",
        "GAC009",
        "GAC010",
        "GAC011",
    ]


def test_rule_requires_a_code_or_all(
    *,
    project: Callable[[dict[str, str]], Path],
) -> None:
    """Neither a code nor `--all` is a usage error (argparse exits 2)."""
    project({"src/mod.py": "x = 1\n"})

    with pytest.raises(SystemExit) as exc:
        main(["rule"])

    assert exc.value.code == 2
