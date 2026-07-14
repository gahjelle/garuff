"""Command-line entry point — parse args, discover the project, lint, report."""

import argparse
import sys
from pathlib import Path

from garuff import branding
from garuff.config import discover_root, load
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.files import discover_git_scope
from garuff.output import (
    render_findings,
    render_parse_failures,
    render_summary,
)
from garuff.rules import REGISTRY
from garuff.runner import run


def main(argv: list[str] | None = None) -> int:
    """Lint the given paths (default: the project root); return the exit code."""
    parser = argparse.ArgumentParser(prog=branding.PROGRAM_NAME)
    parser.add_argument("paths", nargs="*", help="files or directories to lint")
    args = parser.parse_args(argv)

    try:
        root = discover_root(start=Path.cwd())
        scope = discover_git_scope(root, warn=sys.stderr.write)
        config = load(root=root, registry=REGISTRY, scope=scope)
    except (ProjectNotFoundError, ConfigError) as error:
        sys.stderr.write(f"{error}\n")
        return 2

    if args.paths:
        paths = [Path.cwd() / given for given in args.paths]
        if missing := [path for path in paths if not path.exists()]:
            for path in missing:
                sys.stderr.write(f"path does not exist: {path}\n")
            return 2
    else:
        paths = [root]

    result = run(paths=paths, config=config, scope=scope)
    if result.violations or result.directive_errors:
        locators = render_findings(
            violations=result.violations,
            directive_errors=result.directive_errors,
            root=root,
        )
        sys.stdout.write(locators + "\n")
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
