"""Parse garuff's stdout back into structured violations for rule tests.

garuff renders each violation as a locator line — `path:line:col: CODE text`
for source/text scope, `path/: CODE text` for project scope. Rule tests want to
assert on those *as data* (which code, at which location) rather than by
substring. `parse` inverts `output.py`'s render; `LintRun` bundles it with the
run's exit code and raw streams. This parser is coupled to `output.py`'s format;
`tests/test_cli.py`'s raw-line test and `tests/test_lintrun.py`'s round-trip
guard against silent drift between the two.
"""

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class ParsedViolation:
    """One locator line, split into its parts. `line`/`col` are None for scope."""

    path: str
    line: int | None
    col: int | None
    code: str
    message: str


def parse(stdout: str) -> list[ParsedViolation]:
    """Turn garuff's stdout into a list of ParsedViolation, one per locator line."""
    violations: list[ParsedViolation] = []
    for text in stdout.splitlines():
        if not text:
            continue
        locator, _, rest = text.partition(": ")
        code, _, message = rest.partition(" ")
        if locator.endswith("/"):
            path, line, col = locator[:-1], None, None
        else:
            path, line_text, col_text = locator.rsplit(":", 2)
            line, col = int(line_text), int(col_text)
        violations.append(
            ParsedViolation(path=path, line=line, col=col, code=code, message=message)
        )
    return violations


@dataclass(kw_only=True)
class LintRun:
    """The outcome of a run: its exit code, raw streams, and parsed violations."""

    exit_code: int
    stdout: str
    stderr: str
    violations: list[ParsedViolation] = field(init=False)

    def __post_init__(self) -> None:
        """Derive the parsed violations from stdout."""
        self.violations = parse(self.stdout)

    @property
    def codes(self) -> list[str]:
        """Every violation's code, in reported order."""
        return [violation.code for violation in self.violations]

    def at(
        self, path: str, *, line: int | None = None, col: int | None = None
    ) -> list[str]:
        """Return the codes reported at exactly this location (path, line, col)."""
        return [
            violation.code
            for violation in self.violations
            if (violation.path, violation.line, violation.col) == (path, line, col)
        ]
