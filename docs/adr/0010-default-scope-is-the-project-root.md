# Bare `garuff` defaults to the whole project root

ADR-0006 deferred the "honest default" — widening bare `garuff` from
`[src, tests]` to the project root — until file exclusion (#16) and prose
suppression (#4) landed. Both now have, so the default flips: `garuff` with no
paths lints the project root, and #16's two-layer exclusion (dot-dir skip plus
git intersection) keeps `.venv`, `.git`, `.claude`, `.agents`, and gitignored
trees out. This pulls `docs/adr/` (and any `scripts/`/`examples/`) into the
default scope, so the GAA project rules run without being named — while
`[src, tests]` silently skipped them. Scope still follows the given paths
uniformly; only the default widened.

## Consequences

- Bare `garuff` now runs project-scope rules by default (`docs/adr/` is in
  scope).
- The repo's own dogfood collapses from `garuff src tests docs/adr` to bare
  `garuff`.
- Supersedes ADR-0006's "eventual honest default is deferred" note.
