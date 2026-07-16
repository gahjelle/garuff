# GAC007 reads its exempt-modules from garuff config, not ruff's

GAC007 flags a ruff-exempt module imported under `TYPE_CHECKING`. "Exempt" is
defined by ruff's `[tool.ruff.lint.flake8-type-checking].exempt-modules`, but a
`SourceRule.check(module, *, path)` has no access to project config, and garuff
deliberately reads configuration only from its own `[tool.garuff]` table
(`CONTEXT.md`). So GAC007 takes an `exempt_modules: list[str]` **garuff option**
(default empty) under `[tool.garuff.rules.GAC007]`, baked in by `config.load`
like any other per-rule option (ADR-0007) — making it the second configurable
rule and the first with a list-typed option.

## Considered options

- **Read ruff's `exempt-modules` directly.** Rejected: it makes garuff parse
  config outside `[tool.garuff]`, coupling the loader to ruff's config schema and
  breaking the single-config-table invariant. A future reader would reasonably
  expect this and be surprised it is *not* what happens — hence this record.
- **A garuff option (chosen).** Costs the user a small, explicit duplication of
  the module list, but keeps one config table, one validation path, and a rule
  that is inert-by-default (empty list ⇒ never fires) — the safe posture for a
  rule meaningless outside a ruff-configured project.

## Consequences

- The user maintains the exempt list in two places (ruff's and garuff's) if they
  want both tools aligned. Accepted as the honest cost of the invariant.
- `resolve_options` gains list-element validation so a non-string entry is a
  strict config error rather than a silent pass.
