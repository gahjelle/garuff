"""Run pipeline — gather files, parse each once, run source rules, collect."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.rule import SourceRule

if TYPE_CHECKING:
    from garuff.registry import Registry
    from garuff.violation import Violation


def gather_python_files(*, paths: list[Path]) -> list[Path]:
    """Collect the .py files under the given paths, de-duplicated and sorted."""
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(path.rglob("*.py"))
        elif path.suffix == ".py":
            files.add(path)
    return sorted(files)


def run(*, paths: list[Path], registry: Registry) -> list[Violation]:
    """Run every active source rule over the gathered .py files."""
    source_rules = [rule for rule in registry.rules if isinstance(rule, SourceRule)]
    violations: list[Violation] = []
    for file in gather_python_files(paths=paths):
        module = ast.parse(file.read_text())
        for rule in source_rules:
            violations.extend(rule.check(module, path=file))
    return violations
