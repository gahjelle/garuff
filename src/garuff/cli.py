"""Command-line entry point — parse args, discover the project, lint, report."""

import argparse
import sys
from pathlib import Path

from garuff.config import discover_root
from garuff.output import render_summary, render_violations
from garuff.rules import REGISTRY
from garuff.runner import run


def main(argv: list[str] | None = None) -> int:
    """Lint the given paths (default `src/`, `tests/`); return the exit code."""
    parser = argparse.ArgumentParser(prog="garuff")
    parser.add_argument("paths", nargs="*", help="files or directories to lint")
    args = parser.parse_args(argv)

    root = discover_root(start=Path.cwd())
    if args.paths:
        paths = [Path.cwd() / given for given in args.paths]
    else:
        paths = [root / "src", root / "tests"]

    result = run(paths=paths, registry=REGISTRY)
    if result.violations:
        locators = render_violations(violations=result.violations, root=root)
        sys.stdout.write(locators + "\n")
    summary = render_summary(
        linted=result.linted,
        skipped=result.skipped,
        violations=len(result.violations),
    )
    sys.stderr.write(summary + "\n")
    return 1 if result.violations else 0
