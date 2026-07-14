"""Parse garuff's stdout back into structured findings for rule tests.

garuff renders each violation as a locator line — `path:line:col: CODE text`
for source/text scope, `path/: CODE text` for project scope — and each invalid
inline directive as `path:line:col: invalid garuff directive: text` (ADR-0011),
interleaved in the same stream. Rule tests want to assert on those *as data*
(which code, at which location) rather than by substring. `parse` inverts
`output.py`'s render, sorting directive errors out from violations so `codes`
and `at` stay clean; `LintRun` bundles it with the run's exit code and raw
streams. This parser is coupled to `output.py`'s format; `tests/test_cli.py`'s
raw-line test and `tests/test_lintrun.py`'s round-trip guard against silent
drift between the two.
"""

from dataclasses import dataclass, field

from garuff import branding

# The prefix `DirectiveError.render` writes where a violation writes its code.
DIRECTIVE_ERROR_PREFIX = f"invalid {branding.NAME} directive: "


@dataclass(kw_only=True)
class ParsedViolation:
    """One locator line, split into its parts. `line`/`col` are None for scope."""

    path: str
    line: int | None
    col: int | None
    code: str
    message: str


@dataclass(kw_only=True)
class ParsedDirectiveError:
    """One invalid-directive line, split into its parts. Code-less by design."""

    path: str
    line: int | None
    col: int | None
    message: str


@dataclass(kw_only=True)
class ParsedFindings:
    """Every finding on stdout, split by kind."""

    violations: list[ParsedViolation] = field(default_factory=list)
    directive_errors: list[ParsedDirectiveError] = field(default_factory=list)


def parse(stdout: str) -> ParsedFindings:
    """Turn garuff's stdout into parsed violations and directive errors."""
    findings = ParsedFindings()
    for text in stdout.splitlines():
        if not text:
            continue
        locator, _, rest = text.partition(": ")
        if locator.endswith("/"):
            path, line, col = locator[:-1], None, None
        else:
            path, line_text, col_text = locator.rsplit(":", 2)
            line, col = int(line_text), int(col_text)
        if rest.startswith(DIRECTIVE_ERROR_PREFIX):
            findings.directive_errors.append(
                ParsedDirectiveError(
                    path=path,
                    line=line,
                    col=col,
                    message=rest.removeprefix(DIRECTIVE_ERROR_PREFIX),
                )
            )
        else:
            code, _, message = rest.partition(" ")
            findings.violations.append(
                ParsedViolation(
                    path=path, line=line, col=col, code=code, message=message
                )
            )
    return findings


@dataclass(kw_only=True)
class LintRun:
    """The outcome of a run: its exit code, raw streams, and parsed findings."""

    exit_code: int
    stdout: str
    stderr: str
    violations: list[ParsedViolation] = field(init=False)
    directive_errors: list[ParsedDirectiveError] = field(init=False)

    def __post_init__(self) -> None:
        """Derive the parsed findings from stdout."""
        findings = parse(self.stdout)
        self.violations = findings.violations
        self.directive_errors = findings.directive_errors

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
