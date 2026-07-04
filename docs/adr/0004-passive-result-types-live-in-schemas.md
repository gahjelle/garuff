# Passive result and value types live in `schemas.py`

garuff's passive, widely-depended-on data types — `Location`, `Violation`,
`ParseFailure`, and the `RunResult` aggregate — live together in a single leaf
module, `schemas.py`. It imports nothing from the rest of garuff except the
`Rule` type (for `Violation.rule`), so everything else can depend on it without
risking an import cycle. The behaviour-carrying `Rule` hierarchy is deliberately
kept out (see below).

## Considered options

- **Leave each type where it is first produced.** Rejected: this is how the
  asymmetry arose — `Violation` lived in its own module while its structural
  sibling `ParseFailure` (same `Location`, same `render(*, root)`) was buried in
  `runner.py`, so the presentation layer (`output.py`) had to import a type from
  the orchestration layer. Scattering data types across their producers invites
  exactly the circular-import tangles a schema module avoids.
- **A `schemas/` sub-package.** Rejected as premature: the shared set is small
  (four types) and likely to stay small — the types that come later (config
  models, a parsed suppression directive) have a single consumer each and belong
  next to it, not in a shared home. Promoting `schemas.py` to
  `schemas/__init__.py` re-exporting the same names is a mechanical,
  non-breaking move if that day comes, so nothing is lost by starting with a
  file.
- **A single `schemas.py` file (chosen).** One low-dependency module for the
  located, renderable results of a run; the rename from `violation.py` reflects
  that it was already a "located outcomes" module in spirit (it owned
  `Location`).

## Consequences

- **The `Rule` hierarchy stays behavioural, in `rule.py`.** `Rule` looks
  schema-shaped (few dependencies, many dependents) but is the opposite of
  passive data: per [ADR-0003](0003-rules-are-a-nominal-dataclass-hierarchy.md)
  it carries checks, and will grow fixers, config validation, and explanation
  rendering. Only inert result/value types belong in `schemas.py`; anything with
  behaviour does not. This boundary is the load-bearing part of the decision — a
  future contributor should not "tidy" `Rule` into `schemas.py`.
- `runner.py` is reduced to orchestration that *produces* these types rather
  than *defining* them.
