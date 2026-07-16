"""GAC007 type-checking-exempt: a ruff-exempt module stays at runtime.

The exempt set is a garuff option (`exempt-modules`), default empty, so the rule
is inert until a project configures it (ADR-0015). Configured with `["pathlib"]`,
importing `pathlib` under `if TYPE_CHECKING:` is flagged; the same import at
runtime, or a non-exempt module under `TYPE_CHECKING`, is left alone. These cases
run end-to-end through a `.py` file with real config.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff import branding, main

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from tests.lintrun import LintRun


def pyproject(*, exempt: str) -> str:
    """Return `pyproject.toml` text configuring GAC007's exempt-modules list."""
    return (
        '[project]\nname = "sample"\n'
        f"[{branding.CONFIG_TABLE}.rules.GAC007]\n"
        f"exempt-modules = {exempt}\n"
    )


EXEMPT_PATHLIB = pyproject(exempt='["pathlib"]')

PATHLIB_UNDER_TYPE_CHECKING = (
    "from typing import TYPE_CHECKING\n"
    "\n"
    "if TYPE_CHECKING:\n"
    "    from pathlib import Path\n"
)


def test_flags_exempt_module_under_type_checking(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A configured exempt module imported under `TYPE_CHECKING` is flagged GAC007."""
    project(
        {"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": PATHLIB_UNDER_TYPE_CHECKING}
    )

    run = lint(["src"])

    assert run.at("src/mod.py", line=4, col=5) == ["GAC007"]
    assert run.exit_code == 1


def test_flags_exempt_module_under_dotted_type_checking(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The dotted `if typing.TYPE_CHECKING:` guard is recognized too (GAC007)."""
    source = "import typing\n\nif typing.TYPE_CHECKING:\n    from pathlib import Path\n"
    project({"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": source})

    run = lint(["src"])

    assert run.at("src/mod.py", line=4, col=5) == ["GAC007"]
    assert run.exit_code == 1


def test_runtime_import_is_left_alone(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """The same exempt module imported at runtime is not flagged."""
    project(
        {"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": "from pathlib import Path\n"}
    )

    run = lint(["src"])

    assert "GAC007" not in run.codes


def test_non_exempt_module_under_type_checking_is_left_alone(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A module outside the exempt list stays fine under `TYPE_CHECKING`."""
    source = (
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Iterator\n"
    )
    project({"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": source})

    run = lint(["src"])

    assert "GAC007" not in run.codes


def test_rule_is_inert_without_configuration(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """With no exempt-modules configured, GAC007 never fires (default empty list)."""
    project({"src/mod.py": PATHLIB_UNDER_TYPE_CHECKING})

    run = lint(["src"])

    assert "GAC007" not in run.codes


def test_inline_suppression_silences_the_rule(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A `# garuff: ignore[GAC007]` on the import line silences the configured rule."""
    source = (
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from pathlib import Path  # garuff: ignore[GAC007]\n"
    )
    project({"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": source})

    run = lint(["src"])

    assert "GAC007" not in run.codes
    assert run.exit_code == 0


def test_non_string_entry_is_a_config_error(
    *,
    project: Callable[[dict[str, str]], Path],
    lint: Callable[[list[str]], LintRun],
) -> None:
    """A non-string element in exempt-modules aborts with exit 2 (strict config)."""
    project(
        {
            "pyproject.toml": pyproject(exempt='["ok", 1]'),
            "src/mod.py": "x = 1\n",
        }
    )

    run = lint(["src"])

    assert run.exit_code == 2
    assert "exempt-modules" in run.stderr


def test_rule_command_renders_gac007(
    *,
    project: Callable[[dict[str, str]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`garuff rule GAC007` renders the rule in a project configuring exempt-modules."""
    project({"pyproject.toml": EXEMPT_PATHLIB, "src/mod.py": "x = 1\n"})

    code = main(["rule", "GAC007"])

    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("GAC007  ")
