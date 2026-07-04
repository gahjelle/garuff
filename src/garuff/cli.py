"""Command-line entry point — parse args, discover the project, lint, report."""

import argparse
import sys
from pathlib import Path

from garuff.config import discover_root
from garuff.exceptions import ProjectNotFoundError
from garuff.output import (
    render_parse_failures,
    render_summary,
    render_violations,
)
from garuff.rules import REGISTRY
from garuff.runner import run


def main(argv: list[str] | None = None) -> int:
    """Lint the given paths (default `src/`, `tests/`); return the exit code."""
    parser = argparse.ArgumentParser(prog="garuff")
    parser.add_argument("paths", nargs="*", help="files or directories to lint")
    args = parser.parse_args(argv)

    try:
        root = discover_root(start=Path.cwd())
    except ProjectNotFoundError as error:
        sys.stderr.write(f"{error}\n")
        return 2

    if args.paths:
        paths = [Path.cwd() / given for given in args.paths]
        missing = [path for path in paths if not path.exists()]
        if missing:
            for path in missing:
                sys.stderr.write(f"path does not exist: {path}\n")
            return 2
    else:
        paths = [root / "src", root / "tests"]

    result = run(paths=paths, registry=REGISTRY)
    if result.violations:
        locators = render_violations(violations=result.violations, root=root)
        sys.stdout.write(locators + "\n")
    if result.parse_failures:
        failures = render_parse_failures(failures=result.parse_failures, root=root)
        sys.stderr.write(failures + "\n")
    summary = render_summary(
        linted=result.linted,
        skipped=result.skipped,
        violations=len(result.violations),
    )
    sys.stderr.write(summary + "\n")
    return 1 if result.violations or result.parse_failures else 0
