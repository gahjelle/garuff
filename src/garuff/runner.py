"""Run pipeline — gather files, parse each once, run source rules, collect."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.violation import Violation, display_path

if TYPE_CHECKING:
    from garuff.registry import Registry


@dataclass(kw_only=True)
class ParseFailure:
    """A file that could not be parsed, with the location of the failure."""

    path: Path
    line: int
    col: int
    message: str

    def render(self, *, root: Path) -> str:
        """Format as `path:line:col: could not parse: message`."""
        location = f"{display_path(self.path, root=root)}:{self.line}:{self.col}"
        return f"{location}: could not parse: {self.message}"


@dataclass(kw_only=True)
class RunResult:
    """The outcome of a run: violations found, files linted, and files skipped."""

    violations: list[Violation]
    linted: int
    parse_failures: list[ParseFailure] = field(default_factory=list)

    @property
    def skipped(self) -> int:
        """How many files were skipped because they could not be parsed."""
        return len(self.parse_failures)


def gather_python_files(*, paths: list[Path]) -> list[Path]:
    """Collect the .py files under the given paths, de-duplicated and sorted."""
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(path.rglob("*.py"))
        elif path.suffix == ".py":
            files.add(path)
    return sorted(files)


def run(*, paths: list[Path], registry: Registry) -> RunResult:
    """Run every active source rule over the gathered .py files."""
    source_rules = [rule for rule in registry.rules if isinstance(rule, SourceRule)]
    violations: list[Violation] = []
    parse_failures: list[ParseFailure] = []
    linted = 0
    for file in gather_python_files(paths=paths):
        try:
            module = ast.parse(file.read_text())
        except SyntaxError as error:
            parse_failures.append(
                ParseFailure(
                    path=file,
                    line=error.lineno or 1,
                    col=error.offset or 1,
                    message=error.msg,
                ),
            )
            continue
        linted += 1
        for rule in source_rules:
            violations.extend(rule.check(module, path=file))
    return RunResult(
        violations=violations,
        linted=linted,
        parse_failures=parse_failures,
    )
