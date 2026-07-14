"""Run pipeline — gather files, parse each once, run source and text rules."""

import ast
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from garuff.files import GitScope, gather_files
from garuff.rule import ProjectRule, SourceRule, TextRule
from garuff.schemas import (
    DirectiveError,
    Location,
    ParseFailure,
    RunResult,
    Violation,
)
from garuff.suppression import extract

if TYPE_CHECKING:
    from collections.abc import Iterator

    from garuff.config import Config


def suppressed_codes(file: Path, *, config: Config) -> frozenset[str]:
    """Union the codes every `per-file-ignores` entry matching this file silences."""
    return frozenset(
        code
        for entry in config.per_file_ignores
        if entry.matches(file, root=config.root)
        for code in entry.codes
    )


def parse_module(text: str, *, path: Path) -> ast.Module | ParseFailure:
    """Parse a `.py` file's text, returning the failure rather than raising it."""
    try:
        return ast.parse(text)
    except SyntaxError as error:
        return ParseFailure(
            location=Location(path=path, line=error.lineno or 1, col=error.offset or 1),
            message=error.msg,
        )


def source_violations(
    module: ast.Module,
    *,
    path: Path,
    rules: list[SourceRule],
    skip: frozenset[str],
) -> Iterator[Violation]:
    """Yield what every source rule active on this file finds in its syntax tree."""
    for rule in rules:
        if rule.code not in skip:
            yield from rule.check(module, path=path)


def text_violations(
    text: str,
    *,
    path: Path,
    rules: list[TextRule],
    skip: frozenset[str],
) -> Iterator[Violation]:
    """Yield what every text rule active on this file finds in its raw text."""
    for rule in rules:
        if rule.code not in skip:
            yield from rule.check(text, path=path)


def run(*, paths: list[Path], config: Config, scope: GitScope) -> RunResult:
    """Run every active source and text rule over the gathered files.

    Rule selection is per file: a rule whose code a matching `per-file-ignores`
    glob silences does not run on that file. Project rules see only global
    `ignore` (already applied to `config.active`), never per-file-ignores.
    `scope` is git's view of the work-tree, forwarded to `gather_files` so the
    run honours git's exclusions.

    A `.py` file's violations are collected, then filtered against the inline
    directives found in it: source-scope and Python text-scope violations whose
    line carries a matching directive are dropped. Non-`.py` files get no token
    pass, and project rules run outside the loop, so neither is ever suppressed
    inline.
    """
    active = config.active
    source_rules = [rule for rule in active.rules if isinstance(rule, SourceRule)]
    text_rules = [rule for rule in active.rules if isinstance(rule, TextRule)]
    project_rules = [rule for rule in active.rules if isinstance(rule, ProjectRule)]
    violations: list[Violation] = []
    parse_failures: list[ParseFailure] = []
    directive_errors: list[DirectiveError] = []
    linted: Counter[str] = Counter()
    files = gather_files(paths=paths, scope=scope)
    for file in files:
        skip = suppressed_codes(file, config=config)
        text = file.read_text(encoding="utf-8")
        if file.suffix != ".py":
            violations.extend(
                text_violations(text, path=file, rules=text_rules, skip=skip)
            )
            linted[file.suffix] += 1
            continue
        parsed = parse_module(text, path=file)
        if isinstance(parsed, ParseFailure):
            parse_failures.append(parsed)
            continue
        suppressions = extract(text, path=file, known_codes=config.known_codes)
        directive_errors.extend(suppressions.errors)
        found = [
            *source_violations(parsed, path=file, rules=source_rules, skip=skip),
            *text_violations(text, path=file, rules=text_rules, skip=skip),
        ]
        violations.extend(
            violation for violation in found if not suppressions.suppresses(violation)
        )
        linted[file.suffix] += 1
    for rule in project_rules:
        violations.extend(rule.check(files))
    violations.sort(key=lambda v: v.location.sort_key)
    return RunResult(
        violations=violations,
        linted_by_suffix=dict(linted),
        parse_failures=parse_failures,
        directive_errors=directive_errors,
    )
