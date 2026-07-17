"""Command-line entry point — dispatch a subcommand, then lint or explain.

garuff mirrors ruff's shape (ADR-0013): `garuff check [paths]` lints, `garuff
rule <CODE>|--all` explains, and bare `garuff` prints help and exits 2. There is
no default command.
"""

import argparse
import sys
from pathlib import Path

from garuff import branding
from garuff.config import resolve
from garuff.exceptions import ConfigError, ProjectNotFoundError
from garuff.explain import (
    appendix_rules,
    explain_catalog,
    explain_rule,
    resolve_registries,
)
from garuff.output import (
    Verbosity,
    render_appendix,
    render_explanations,
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
    check_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="drop the run summary; findings and diagnostics still print",
    )
    check_parser.add_argument(
        "--fix",
        action="store_true",
        help="apply available fixers, then report only what remains",
    )

    rule_parser = subparsers.add_parser("rule", help="explain a rule (or all rules)")
    rule_parser.add_argument("code", nargs="?", help="the rule code to explain")
    rule_parser.add_argument("--all", action="store_true", help="explain every rule")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    if args.command == "rule":
        return explain(code=args.code, all_rules=args.all, parser=rule_parser)
    return check(
        paths=args.paths,
        verbosity=Verbosity.QUIET if args.quiet else Verbosity.DEFAULT,
        fix=args.fix,
    )


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
        catalog, active = resolve_registries(
            start=Path.cwd(), registry=REGISTRY, warn=sys.stderr.write
        )
    except ConfigError as error:
        sys.stderr.write(f"{error}\n")
        return 2

    if all_rules:
        selected = explain_catalog(catalog=catalog, active=active)
        sys.stdout.write(render_explanations(selected) + "\n")
        return 0
    if code is None:
        parser.error("a rule code or --all is required")
    if code not in catalog.by_code:
        message = f"unknown rule code: {code}"
        if tip := catalog.suggest(code):
            message += f" (did you mean {tip}?)"
        sys.stderr.write(message + "\n")
        return 2
    selected = [explain_rule(code, catalog=catalog, active=active)]
    sys.stdout.write(render_explanations(selected) + "\n")
    return 0


def check(*, paths: list[str], verbosity: Verbosity, fix: bool = False) -> int:
    """Lint the given paths (default: the project root); return the exit code.

    `verbosity` gates only garuff's own status output: under `Verbosity.QUIET`
    the run summary is dropped, while findings and diagnostics (parse failures,
    the git-scope warning, config/path errors) still print. It never changes the
    returned exit code.

    Under `fix`, available fixers are applied per file before violations are
    collected, so only the unfixable remainder is reported and the exit code is
    computed on it. A `--fix` run adds a fixes clause to the summary (even `0`);
    a normal run omits it entirely.
    """
    try:
        config, scope = resolve(
            start=Path.cwd(), registry=REGISTRY, warn=sys.stderr.write
        )
    except (ProjectNotFoundError, ConfigError) as error:
        sys.stderr.write(f"{error}\n")
        return 2
    root = config.root

    if paths:
        resolved = [Path.cwd() / given for given in paths]
        if missing := [path for path in resolved if not path.exists()]:
            for path in missing:
                sys.stderr.write(f"path does not exist: {path}\n")
            return 2
    else:
        resolved = [root]

    result = run(paths=resolved, config=config, scope=scope, fix=fix)
    if result.violations or result.directive_errors:
        locators = render_findings(
            violations=result.violations,
            directive_errors=result.directive_errors,
            root=root,
        )
        sys.stdout.write(locators + "\n")
        appendix = render_appendix(appendix_rules(violations=result.violations))
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
        fixes=result.fixes_applied if fix else None,
    )
    if verbosity >= Verbosity.DEFAULT:
        sys.stderr.write(summary + "\n")
    return (
        1
        if result.violations or result.parse_failures or result.directive_errors
        else 0
    )
