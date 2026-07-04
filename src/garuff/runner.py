"""Run pipeline — gather files, parse each once, run source rules, collect."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule
from garuff.violation import Violation

if TYPE_CHECKING:
    from garuff.registry import Registry


@dataclass(kw_only=True)
class RunResult:
    """The outcome of a run: the violations found and how many files were seen."""

    violations: list[Violation]
    linted: int
    skipped: int = 0


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
    linted = 0
    for file in gather_python_files(paths=paths):
        module = ast.parse(file.read_text())
        linted += 1
        for rule in source_rules:
            violations.extend(rule.check(module, path=file))
    return RunResult(violations=violations, linted=linted)
