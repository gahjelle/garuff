"""GAA002 — ADR numbers must be a gapless run from 0001."""

from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import ProjectRule
from garuff.rules.agent.adr import iter_adr_groups
from garuff.schemas import Location, Violation

if TYPE_CHECKING:
    from collections.abc import Iterator


class AdrConsecutiveNumbers(ProjectRule):
    """Flag an ADR directory whose numbers are not a gapless run from 0001."""

    def check(self, project_files: list[Path]) -> Iterator[Violation]:
        """Yield one violation per ADR directory whose numbering has a gap."""
        for adr_dir, entries in iter_adr_groups(project_files).items():
            present = sorted({number for number, _ in entries})
            if not present or present == list(range(1, len(present) + 1)):
                continue
            got = ", ".join(f"{n:04d}" for n in present)
            expected = f"0001\N{EN DASH}{len(present):04d}"
            yield Violation(
                rule=self,
                location=Location(path=adr_dir),
                detail=(
                    "ADR numbers must be a gapless run from 0001; "
                    f"got {got}, expected {expected}"
                ),
            )


ADR_CONSECUTIVE = AdrConsecutiveNumbers(
    code="GAA002",
    summary="ADR numbers must be a gapless run from 0001",
)
