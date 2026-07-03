# garuff has zero runtime dependencies

garuff is a linter installed into every project's dev and CI environment, so we
hold "zero runtime dependencies" as a deliberate constraint: it uses only the
standard library at runtime. Config is parsed with `tomllib` and validated by
hand against per-rule `@dataclass(kw_only=True)` option schemas, rather than with
a validation library.

## Considered options

- **Validate config with pydantic.** Tempting, since garuff's own rules are
  *about* pydantic (`FrozenModel`/`StrictModel`) and `extra="forbid"` gives
  strict unknown-key errors for free. Rejected: it adds a compiled runtime
  dependency (pydantic-core) to every environment garuff touches, to validate a
  handful of config keys. Being *about* pydantic does not require *depending* on
  it.
- **Stdlib only (chosen).** The config surface is tiny — `ignore`,
  `per-file-ignores`, and a few scalar per-rule options. Hand-rolled validation
  is small, keeps install friction and startup time minimal, and gives exact
  control over the strict, agent-readable error messages garuff promises.

## Consequences

- New features must justify any dependency against this constraint; the default
  answer is "use the standard library."
- garuff can be dropped into any Python project without dependency-resolution
  friction — the property that makes an install-everywhere linter viable.
