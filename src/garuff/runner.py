"""Run pipeline — gather files, parse each once, run source and text rules."""

import ast
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from garuff.rule import ProjectRule, SourceRule, TextRule
from garuff.schemas import Location, ParseFailure, RunResult, Violation

if TYPE_CHECKING:
    from garuff.config import Config

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


def suppressed_codes(file: Path, *, config: Config) -> frozenset[str]:
    """Union the codes every `per-file-ignores` glob matching this file silences.

    The file is matched by its root-relative POSIX path, so globs are anchored to
    the project root and `**` crosses directory segments on every platform.
    """
    relative = PurePosixPath(file.relative_to(config.root).as_posix())
    return frozenset(
        code
        for glob, codes in config.per_file_ignores
        if relative.full_match(glob)
        for code in codes
    )


def run(*, paths: list[Path], config: Config) -> RunResult:
    """Run every active source and text rule over the gathered files.

    Rule selection is per file: a rule whose code a matching `per-file-ignores`
    glob silences does not run on that file. Project rules see only global
    `ignore` (already applied to the resolved registry), never per-file-ignores.
    """
    registry = config.registry
    source_rules = [rule for rule in registry.rules if isinstance(rule, SourceRule)]
    text_rules = [rule for rule in registry.rules if isinstance(rule, TextRule)]
    project_rules = [rule for rule in registry.rules if isinstance(rule, ProjectRule)]
    violations: list[Violation] = []
    parse_failures: list[ParseFailure] = []
    linted: Counter[str] = Counter()
    files = gather_files(paths=paths)
    for file in files:
        skip = suppressed_codes(file, config=config)
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
                if rule.code not in skip:
                    violations.extend(rule.check(module, path=file))
        for rule in text_rules:
            if rule.code not in skip:
                violations.extend(rule.check(text, path=file))
        linted[file.suffix] += 1
    for rule in project_rules:
        violations.extend(rule.check(files))
    violations.sort(key=lambda v: v.location.sort_key)
    return RunResult(
        violations=violations,
        linted_by_suffix=dict(linted),
        parse_failures=parse_failures,
    )
