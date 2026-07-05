"""`iter_adr_groups`: which files count as ADRs, and how they group by directory."""

from pathlib import Path

from garuff.rules.agent.adr import iter_adr_groups


def test_groups_adr_files_by_containing_directory() -> None:
    """ADR files under a `docs/adr/` directory group together by number."""
    files = [
        Path("docs/adr/0001-a.md"),
        Path("docs/adr/0002-b.md"),
    ]

    groups = iter_adr_groups(files)

    assert groups == {
        Path("docs/adr"): [
            (1, Path("docs/adr/0001-a.md")),
            (2, Path("docs/adr/0002-b.md")),
        ],
    }


def test_ignores_files_that_are_not_adrs() -> None:
    """`README.md`, non-4-digit prefixes, and non-adr-directory files are ignored."""
    files = [
        Path("docs/adr/README.md"),
        Path("docs/adr/template.md"),
        Path("docs/adr/1-x.md"),
        Path("docs/adr/0001-x.txt"),
        Path("src/garuff/schemas.py"),
    ]

    groups = iter_adr_groups(files)

    assert groups == {}
