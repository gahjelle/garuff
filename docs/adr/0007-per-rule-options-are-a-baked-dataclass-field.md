# Per-rule options are a baked-in dataclass field, resolved before the run

A configurable rule declares an explicit nested `Options` `@dataclass(kw_only=True)`
and holds it as an `options` field (optionless rules declare no such field).
`config.load` validates the `[tool.garuff.rules.<CODE>]` table against that
schema and bakes overrides in with `dataclasses.replace(rule, options=…)`,
producing a *resolved* registry; a rule's `check` reads `self.options` and its
signature never changes. The same resolution step removes globally-`ignore`d
rules, so the runner receives a registry it can run wholesale — it never sees
options or raw config.

## Considered options

- **Thread a separate options object into `check`** (`check(module, *, path,
  options)`). Rejected: it grows *every* rule's `check` signature — including the
  majority that will never be configurable — forces a shared empty `Options` onto
  optionless rules, and needs a `code → Options` sidecar that the runner consults
  on every call. The moment you instead *apply* each `Options` onto its rule to
  avoid that plumbing, you have arrived at the baked-field design below.
- **Bake options into the rule instance (chosen).** The rule *is* its resolved
  options. `dataclasses.replace` yields a fresh instance, so the module-level
  singleton is untouched and runs cannot leak into one another. The `Options`
  dataclass doubles as the validation schema (`fields(type(rule.options))`),
  keeping hand-rolled validation (ADR-0002) close to the thing it validates.

## Consequences

- The runner is entirely options-agnostic: it splits the resolved registry by
  scope and runs each rule's `check`. Both levers — global `ignore` and per-rule
  options — are resolved in `config.load`, not the runner.
- "Is this rule configurable?" is answered by the *presence* of an `options`
  field. A `[tool.garuff.rules.<CODE>]` table for a rule without one is a config
  error; base `Rule` identity fields (`code`, `summary`, …) are never
  configurable because they are not part of any `Options` schema.
- Adding options to a rule is local: declare an `Options` dataclass, add the
  `options` field, read `self.options` in `check`. No engine change — consistent
  with the forkable engine/opinion seam (ADR-0005).
