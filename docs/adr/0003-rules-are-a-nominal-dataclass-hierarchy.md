# Rules are a nominal dataclass hierarchy, not protocols

A rule is modelled as a concrete `@dataclass(kw_only=True)` base `Rule` (carrying
the scope-independent identity and explanation — `code`, `summary`, later
`rationale`/`fix`/config schema) with scope subclasses (`SourceRule`, and later
`TextRule`/`ProjectRule`) that inherit those fields and add a scope-specific
`check` method. Scope classes are abstract (`abc.ABC` + `@abstractmethod`) so
that instantiating a scope without implementing `check` fails at construction
time, not at run time. Concrete rules subclass the scope class; the explicit
registry holds them as `Rule`.

## Considered options

- **Composition — a `SourceRule` instance holding a `check` callable field.**
  Rejected: as rules grow an optional fixer and per-rule config schema, the
  behaviour scatters across parallel `Callable` fields and free functions that
  all take `rule` as a first argument, instead of living together in one class.
- **`Protocol` (structural typing).** Rejected for two reasons. (1) A Protocol
  carries no implementation, but a `Rule` base is exactly where shared behaviour
  will live — dataclass field inheritance for every scope, hand-rolled config
  validation (ADR-0002), category-prefix checks, explanation rendering. It would
  become "Protocol + mixin," the worst of both. (2) Protocols pay off with
  independent third-party implementers; garuff is deliberately a closed,
  first-party, explicitly-aggregated registry with no plugins or
  auto-discovery — the coupling a Protocol removes is coupling we want.
- **Nominal dataclass hierarchy (chosen).** One known base per rule, behaviour
  co-located as the rule deepens, one nominal type for the registry to iterate
  and filter by `code` before it cares about scope.

## Consequences

- The class split mirrors the glossary: `Rule` = the addressable unit
  (identity + explanation), rule **scope** = the kind of input the check
  consumes.
- The `check` seam (`check(self, module: ast.Module, path: Path)` for source
scope) is load-bearing: every rule is written against it, so changing its
signature later is a breaking change across the whole rule set.
- Scope classes are abstract (`abc.ABC`) to prevent partial rules from
entering the registry — a missing `check` override is caught at instantiation,
not during a lint run.
