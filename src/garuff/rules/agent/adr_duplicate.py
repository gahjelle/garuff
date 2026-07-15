"""GAA001 — duplicate ADR numeric prefix."""

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import ProjectRule
from garuff.rules.agent.adr import iter_adr_groups
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


class AdrDuplicatePrefix(ProjectRule):
    """Flag ADR numbers shared by more than one file in the same directory."""

    def check(self, project_files: list[Path]) -> Iterator[Violation]:
        """Yield one violation per duplicated ADR number, per directory."""
        for adr_dir, entries in iter_adr_groups(project_files).items():
            counts = Counter(number for number, _ in entries)
            for number, count in sorted(counts.items()):
                if count <= 1:
                    continue
                names = ", ".join(
                    sorted(path.name for n, path in entries if n == number)
                )
                yield Violation(
                    rule=self,
                    location=Location(path=adr_dir),
                    detail=f"duplicate ADR number {number:04d}: {names}",
                )


ADR_DUPLICATE = AdrDuplicatePrefix(
    code="GAA001",
    summary="duplicate ADR numeric prefix",
    rationale="""
        An ADR's number is its identity — decisions cite each other by it
        ("supersedes ADR-0004"). Two files sharing a number make every citation
        ambiguous.
    """,
    fix="""
        Renumber one of the colliding files to the next free number, keeping the
        four-digit prefix:
            docs/adr/0004-a.md
            docs/adr/0004-b.md  ->  docs/adr/0005-b.md
    """,
)
