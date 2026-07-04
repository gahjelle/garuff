# garuff — initial structure plan

Design settled in a grilling session. Vocabulary lives in `CONTEXT.md`; the
load-bearing decisions are recorded as ADRs. This file is the implementation
blueprint, not a spec of behaviour.

## Decisions (summary)

- **First-class rules + explicit registry.** Each rule is a self-describing
  object; `rules/__init__.py` aggregates them explicitly (no decorator
  auto-discovery).
- **Category prefixes by subject matter.** `GAC` = code rules (Python + its
  prose), `GAA` = agent-file rules (repository scaffolding, e.g. ADRs).
  Renumbered contiguously from the old `WNG*`: `GAC001–011`, `GAA001–002`.
- **Three rule scopes.** `source` (per-`.py` AST), `text` (raw text, any
  extension), `project` (whole structure, checked once).
- **Configuration** in `[tool.garuff]`, addressed by code only:
  - `ignore = [...]` — global, all rules on by default. Only way to silence a
    project-scope rule.
  - `[tool.garuff.rules.<CODE>]` — per-rule options (e.g. `max-positional-args`).
  - `[tool.garuff.per-file-ignores]` — glob → codes.
  - Strict: unknown key/code, wrong type, and empty globs all error.
- **Inline suppression** — `# garuff: ignore[GAC009]` (codes required, no bare
  form). Source-scope and Python text-scope only; never project-scope or
  Markdown. See ADR-0001.
- **Zero runtime dependencies** — stdlib only; config validated by hand against
  per-rule `@dataclass(kw_only=True)` schemas. See ADR-0002.
- **Agent-first messages** — every rule carries `summary` / `rationale` / `fix`.
  Default output = locator lines + each fired rule explained once (appendix).
  `garuff explain <CODE>` renders the same text on demand.
- **Project discovery** — walk up to the nearest `pyproject.toml`; that
  directory is the project root. Config optional, file required. No
  `--config`/`--root` flag for now.

## Package layout

```
src/garuff/
├── __init__.py        # main() — thin shim into cli
├── cli.py             # argparse: default lint command + `explain` subcommand; exit codes
├── violation.py       # Violation dataclass + terse-line rendering
├── rule.py            # SourceRule / TextRule / ProjectRule
│                      #   shared: code, summary, rationale, fix, config schema, optional fixer
├── registry.py        # collects all rules; lookup by code; strict "unknown code" authority
├── config.py          # discover root; parse+validate [tool.garuff]; resolve ignore /
│                      #   per-file-ignores / per-rule dataclass options
├── suppression.py     # parse `# garuff: ignore[...]` via tokenize; filter violations
├── runner.py          # orchestration (pipeline below)
├── output.py          # violation lines + explain-each-fired-rule-once appendix
└── rules/
    ├── __init__.py    # aggregates every rule into the registry
    ├── code/          # GAC — source & text scope (GAC001–011)
    └── agent/         # GAA — project scope (GAA001–002)
```

## Run pipeline (`runner.py`)

1. `cli` parses args → lint (default) or `explain CODE`.
2. `config.discover()` — nearest `pyproject.toml` = root; load & strictly
   validate `[tool.garuff]` before any linting.
3. Gather files under the given paths (default `src/`, `tests/`, root-relative).
4. Per `.py`: parse AST once → run active source rules; run active text rules on
   the raw source.
5. Per other linted file (`.md`): run active text rules.
6. Run active project rules once (e.g. ADR rules against `root/docs/adr`).
7. Filter: global `ignore`, `per-file-ignores` globs, and inline directives.
   Project-scope violations see only global `ignore`.
8. `output` prints locator lines + rationale/fix appendix per fired rule.
9. Exit `0` clean / `1` violations / `2` config error.

`--fix` applies per-rule fixers (text rewrites) before step 7.

## Deferred on purpose

Bare `# garuff: ignore`; Markdown inline suppression; unused-directive detection
(a future rule); `--config`/`--root` flags; `select`/allowlist mode; JSON output.

File exclusion (gitignore-aware selection, hidden-directory / `.venv` /
vendored-tree skipping). Until then, `rglob("*.py")` lints everything under the
given paths; the default `src/`/`tests/` paths make this safe in practice, but
pointing garuff at a tree containing a virtualenv would lint it.
