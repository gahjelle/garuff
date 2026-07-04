# garuff separates a generic engine from an opinion layer, and is forkable

garuff's rules are one person's opinions, which others need not share. A side
goal is therefore that the project be **forkable**: the linting engine is kept
opinion-agnostic, and all the actual conventions live in `src/garuff/rules/`, so
someone can fork the repo, replace `rules/`, and have their own linter with the
same machinery.

## The seam

- **Opinion layer** — `src/garuff/rules/` and its explicit aggregation in
  `rules/__init__.py`. This is what a fork replaces.
- **Engine** — everything else (`rule.py`, `registry.py`, `config.py`,
  `suppression.py`, `runner.py`, `schemas.py`, `output.py`, `cli.py`). None of
  it hardcodes *which* rules exist: `cli.py` reaches the rules only through the
  single `from garuff.rules import REGISTRY` seam, the registry indexes whatever
  codes rules declare (no baked-in `GAC`/`GAA`), and per-rule config is resolved
  by code lookup, not by a hardcoded list.

## Two levels of fork

- **Level A — rules-only fork** (keep the `garuff` name): works today, with zero
  engine changes. This is the realistic, cheap path.
- **Level B — rebranded fork** (a fork's own tool name): four branding literals
  are still threaded through the engine as bare strings — the package name
  `garuff`, the inline directive prefix (see
  [ADR-0001](0001-namespaced-suppression-directive.md)), the `[tool.garuff]`
  config table, and the CLI `prog`. Collapsing the last three into one module so
  a rebrand is a one-edit change is tracked as a follow-up (#18); the package
  rename stays a manual step.

## Consequences

- **Rule logic must not leak into the engine.** The engine modules stay free of
  any specific convention; a new rule is added under `rules/` and registered in
  `rules/__init__.py`, never by special-casing it in `runner.py` or elsewhere.
  This is the property the ADR exists to protect.
- Category prefixes (`GAC`/`GAA`) are just strings rules carry, not engine
  constants — a fork picks its own.
