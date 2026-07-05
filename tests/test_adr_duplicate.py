"""GAA001: duplicate ADR numeric prefix."""

from pathlib import Path

from garuff.rules.agent.adr_duplicate import ADR_DUPLICATE


def test_no_adr_directory_is_a_silent_no_op() -> None:
    """No `docs/adr/` in the gathered files means no violations at all."""
    files = [Path("src/garuff/schemas.py")]

    assert list(ADR_DUPLICATE.check(files)) == []


def test_clean_run_yields_no_violations() -> None:
    """Distinct ADR numbers in one directory produce no violations."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0002-b.md"),
    ]

    assert list(ADR_DUPLICATE.check(files)) == []


def test_duplicate_number_yields_one_violation_naming_the_colliders() -> None:
    """Two files sharing a number yield one violation at the ADR directory."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0001-b.md"),
        Path("docs/adr/0003-c.md"),
    ]

    violations = list(ADR_DUPLICATE.check(files))

    assert len(violations) == 1
    violation = violations[0]
    assert violation.location.path == Path("docs/adr")
    assert violation.location.line is None
    assert violation.detail == "duplicate ADR number 0001: 0001-a.md, 0001-b.md"
