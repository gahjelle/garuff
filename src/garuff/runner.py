"""Run pipeline — gather files, parse each once, run source and text rules."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule, TextRule
from garuff.schemas import Location, ParseFailure, RunResult, Violation

if TYPE_CHECKING:
    from garuff.registry import Registry

# The file extensions garuff lints. Source rules run on `.py` only; text rules
# run on the raw text of every gathered file.
LINTED_SUFFIXES = frozenset({".py", ".md"})


def gather_files(*, paths: list[Path]) -> list[Path]:
    """Collect the linted files under the given paths, de-duplicated and sorted."""
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(
                found
                for found in path.rglob("*")
                if found.suffix in LINTED_SUFFIXES and found.is_file()
            )
        elif path.suffix in LINTED_SUFFIXES:
            files.add(path)
    return sorted(files)


def run(*, paths: list[Path], registry: Registry) -> RunResult:
    """Run every active source and text rule over the gathered files."""
    source_rules = [rule for rule in registry.rules if isinstance(rule, SourceRule)]
    text_rules = [rule for rule in registry.rules if isinstance(rule, TextRule)]
    violations: list[Violation] = []
    parse_failures: list[ParseFailure] = []
    linted = 0
    for file in gather_files(paths=paths):
        text = file.read_text(encoding="utf-8")
        if file.suffix == ".py":
            try:
                module = ast.parse(text)
            except SyntaxError as error:
                parse_failures.append(
                    ParseFailure(
                        location=Location(
                            path=file,
                            line=error.lineno or 1,
                            col=error.offset or 1,
                        ),
                        message=error.msg,
                    ),
                )
                continue
            for rule in source_rules:
                violations.extend(rule.check(module, path=file))
        for rule in text_rules:
            violations.extend(rule.check(text, path=file))
        linted += 1
    violations.sort(key=locator_key)
    return RunResult(
        violations=violations,
        linted=linted,
        parse_failures=parse_failures,
    )


def locator_key(violation: Violation) -> tuple[str, int, int]:
    """Sort key placing violations in `path`, then line, then column order."""
    location = violation.location
    return (str(location.path), location.line, location.col)
