"""Command-line entry point — dispatch a subcommand, then lint or explain.

garuff mirrors ruff's shape (ADR-0013): `garuff check [paths]` lints, `garuff
rule <CODE>|--all` explains, and bare `garuff` prints help and exits 2. There is
no default command.
"""

import argparse
import sys
from pathlib import Path

from garuff import branding
from garuff.config import discover_root, load
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.files import discover_git_scope
from garuff.output import (
    render_appendix,
    render_findings,
    render_parse_failures,
    render_summary,
)
from garuff.rules import REGISTRY
from garuff.runner import run


def main(argv: list[str] | None = None) -> int:
    """Dispatch to a subcommand; bare `garuff` prints help and exits 2."""
    parser = argparse.ArgumentParser(prog=branding.PROGRAM_NAME)
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="lint the given paths")
    check_parser.add_argument("paths", nargs="*", help="files or directories to lint")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    return check(paths=args.paths)


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
