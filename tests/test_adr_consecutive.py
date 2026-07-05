"""GAA002: ADR numbers must be a gapless run from 0001."""

from pathlib import Path

from garuff.rules.agent.adr_consecutive import ADR_CONSECUTIVE


def test_no_adr_directory_is_a_silent_no_op() -> None:
    """No `docs/adr/` in the gathered files means no violations at all."""
    files = [Path("src/garuff/schemas.py")]

    assert list(ADR_CONSECUTIVE.check(files)) == []


def test_clean_gapless_run_yields_no_violations() -> None:
    """A gapless run from 0001 produces no violations."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0002-b.md"),
        Path("docs/adr/0003-c.md"),
    ]

    assert list(ADR_CONSECUTIVE.check(files)) == []


def test_duplicate_numbers_alone_do_not_trigger_gaa002() -> None:
    """A duplicated number with an otherwise gapless set of numbers is fine."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0001-b.md"),
        Path("docs/adr/0002-c.md"),
    ]

    assert list(ADR_CONSECUTIVE.check(files)) == []


def test_gap_yields_one_violation_with_got_and_expected() -> None:
    """A gap in numbering yields one violation at the ADR directory."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0003-c.md"),
    ]

    violations = list(ADR_CONSECUTIVE.check(files))

    assert len(violations) == 1
    violation = violations[0]
    assert violation.location.path == Path("docs/adr")
    assert violation.location.line is None
    assert violation.detail == (
        "ADR numbers must be a gapless run from 0001; "
        "got 0001, 0003, expected 0001\N{EN DASH}0002"
    )


def test_missing_0001_yields_violation() -> None:
    """Numbering that skips 0001 entirely is flagged."""
    files = [
        Path("docs/adr/0002-b.md"),
        Path("docs/adr/0003-c.md"),
    ]

    violations = list(ADR_CONSECUTIVE.check(files))

    assert len(violations) == 1
    assert violations[0].detail == (
        "ADR numbers must be a gapless run from 0001; "
        "got 0002, 0003, expected 0001\N{EN DASH}0002"
    )
