# Project-scope rules run over the gathered files, honestly bounded by paths

*Status: the deferred "honest default" note below is superseded by ADR-0010 —
bare `garuff` now defaults to the project root.*

The obvious reading of project scope — and the original tracer #3 wording — was
"run project rules once against the discovered **root**." We rejected that:
passing `garuff src/` would then report `docs/adr/` violations that live nowhere
near `src/`, which is dishonest. Instead a `ProjectRule` receives the same
already-gathered file list every other scope sees (`check(project_files)`), and
filters it to what it cares about. Scope follows the given paths for *all* rule
scopes uniformly, with no special "always scan root" pass and no `root`
parameter.

## Consequences

- **Honesty is automatic.** `garuff src/` gathers nothing under `docs/adr/`, so
  the ADR rules (GAA001/GAA002) silently no-op. No path filtering logic in the
  runner, no per-rule I/O — a project rule is a pure function of the gathered
  files.
- **Rules group by directory, not a hardcoded `root/docs/adr`.** GAA001/GAA002
  group ADR files by their containing directory and check each group, which also
  makes them correct for the multi-context repos the domain model anticipates
  (per-context `docs/adr/`).
- **Bare `garuff` does not run project rules by default.** The default paths are
  `[src, tests]`, so `docs/adr/` is out of scope unless named. This repo's own
  dogfood therefore runs `garuff src docs/adr`.
- **The eventual honest default is deferred, not designed away.** Making bare
  `garuff` lint the whole project (so it catches `scripts/`, `examples/`, and
  `docs/adr/` at once) requires file exclusion — skipping `.venv`, `.git`,
  vendored trees — which is its own design pass (#16), and prose suppression for
  the possessive-`my` rule, which is config work (#4). Once both land, the
  default flips from `[src, tests]` to the project root and everything composes:
  scope still follows paths, the default just widens. — done in ADR-0010; bare
  `garuff` now defaults to the project root.
