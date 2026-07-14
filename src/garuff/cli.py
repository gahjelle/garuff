"""Command-line entry point — dispatch a subcommand, then lint or explain.

garuff mirrors ruff's shape (ADR-0013): `garuff check [paths]` lints, `garuff
rule <CODE>|--all` explains, and bare `garuff` prints help and exits 2. There is
no default command.
"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from garuff import branding
from garuff.config import discover_root, load
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.files import discover_git_scope
from garuff.output import (
    render_appendix,
    render_explanation,
    render_findings,
    render_parse_failures,
    render_summary,
)
from garuff.rules import REGISTRY
from garuff.runner import run

if TYPE_CHECKING:
    from garuff.registry import Registry

# The note appended to an ignored rule's explanation by `garuff rule`.
IGNORED_NOTE = "ignored in this project's configuration"


def main(argv: list[str] | None = None) -> int:
    """Dispatch to a subcommand; bare `garuff` prints help and exits 2."""
    parser = argparse.ArgumentParser(prog=branding.PROGRAM_NAME)
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="lint the given paths")
    check_parser.add_argument("paths", nargs="*", help="files or directories to lint")

    rule_parser = subparsers.add_parser("rule", help="explain a rule (or all rules)")
    rule_parser.add_argument("code", nargs="?", help="the rule code to explain")
    rule_parser.add_argument("--all", action="store_true", help="explain every rule")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    if args.command == "rule":
        return explain(code=args.code, all_rules=args.all, parser=rule_parser)
    return check(paths=args.paths)


def explain(
    *, code: str | None, all_rules: bool, parser: argparse.ArgumentParser
) -> int:
    """Explain one rule, or every rule with `--all`, reading the project config.

    The catalog (options baked) comes from the project when there is one, or the
    defaults outside a project; either way an ignored rule stays explainable and
    is flagged with a note. A broken config aborts with exit 2 — the options are
    unknowable without it.
    """
    try:
        catalog, active = resolve_registries()
    except ConfigError as error:
        sys.stderr.write(f"{error}\n")
        return 2

    if all_rules:
        blocks = [
            render_explanation(
                rule.explanation, note=note_for(rule.code, active=active)
            )
            for _, rule in sorted(catalog.by_code.items())
        ]
        sys.stdout.write("\n\n".join(blocks) + "\n")
        return 0
    if code is None:
        parser.error("a rule code or --all is required")
    if code not in catalog.by_code:
        message = f"unknown rule code: {code}"
        if tip := catalog.suggest(code):
            message += f" (did you mean {tip}?)"
        sys.stderr.write(message + "\n")
        return 2
    rule = catalog.by_code[code]
    block = render_explanation(rule.explanation, note=note_for(code, active=active))
    sys.stdout.write(block + "\n")
    return 0


def resolve_registries() -> tuple[Registry, Registry]:
    """Return the (catalog, active) registries for the current directory.

    Inside a project both come from its validated config; outside any project
    both are the defaults, so a rule still explains at its default options.
    """
    try:
        root = discover_root(start=Path.cwd())
    except ProjectNotFoundError:
        return REGISTRY, REGISTRY
    scope = discover_git_scope(root, warn=sys.stderr.write)
    config = load(root=root, registry=REGISTRY, scope=scope)
    return config.registry, config.active


def note_for(code: str, *, active: Registry) -> str | None:
    """Return the ignored-rule note when this code is not in the active set."""
    return None if code in active.by_code else IGNORED_NOTE


def check(*, paths: list[str]) -> int:
    """Lint the given paths (default: the project root); return the exit code."""
    try:
        root = discover_root(start=Path.cwd())
        scope = discover_git_scope(root, warn=sys.stderr.write)
        config = load(root=root, registry=REGISTRY, scope=scope)
    except (ProjectNotFoundError, ConfigError) as error:
        sys.stderr.write(f"{error}\n")
        return 2

    if paths:
        resolved = [Path.cwd() / given for given in paths]
        if missing := [path for path in resolved if not path.exists()]:
            for path in missing:
                sys.stderr.write(f"path does not exist: {path}\n")
            return 2
    else:
        resolved = [root]

    result = run(paths=resolved, config=config, scope=scope)
    if result.violations or result.directive_errors:
        locators = render_findings(
            violations=result.violations,
            directive_errors=result.directive_errors,
            root=root,
        )
        sys.stdout.write(locators + "\n")
        appendix = render_appendix(violations=result.violations)
        if appendix:
            sys.stdout.write("\n" + appendix + "\n")
    if result.parse_failures:
        failures = render_parse_failures(failures=result.parse_failures, root=root)
        sys.stderr.write(failures + "\n")
    summary = render_summary(
        linted_by_suffix=result.linted_by_suffix,
        skipped=result.skipped,
        violations=len(result.violations),
        directive_errors=len(result.directive_errors),
    )
    sys.stderr.write(summary + "\n")
    return (
        1
        if result.violations or result.parse_failures or result.directive_errors
        else 0
    )
