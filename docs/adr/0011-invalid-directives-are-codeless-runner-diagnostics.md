# Invalid inline directives are code-less runner diagnostics, not rules

An inline suppression directive (`# garuff: ignore[...]`, ADR-0001) can be wrong
in two ways garuff must surface rather than silently swallow: it can name an
**unknown code** (`ignore[GAC999]`), or it can be **malformed** (no brackets,
empty brackets, unclosed). The question is what *kind* of thing that report is.

garuff already has three ways to tell the user something is wrong, and none fit:

- **`ConfigError` → exit 2**, raised *before* the run. Wrong: a directive is
  discovered *during* the run, per file. One bad directive in one file must not
  abort the whole lint, the way an invalid config table does.
- **`Violation` → exit 1, stdout.** A `Violation` requires a `Rule` (a `code`
  and `summary`). There is no rule here. Minting a real meta-rule — say a
  `GACxxx` "invalid directive" rule — is paradoxical: a suppression-validator
  rule could be silenced by the very mechanism it polices (`# garuff:
  ignore[GACxxx]`), and could itself be globally `ignore`d, defeating the point.
- **`ParseFailure` → exit 1, stderr.** Structurally the closest (a located,
  code-less diagnostic with a message), but a parse failure is operational noise
  about a file garuff *could not read*, routed to stderr. A bad directive is a
  finding about code the user *wrote at a specific spot* — it belongs in the
  findings stream on stdout, next to violations.

## Decision

Invalid directives are reported through a new **`DirectiveError`** — a located,
**code-less** diagnostic (`location` + `message`) that lives in `schemas.py`
beside `Violation` and `ParseFailure`, is carried on `RunResult` in its own list,
renders to **stdout** interleaved with violations by location, and contributes to
**exit 1**. It is deliberately *not* a rule: the runner produces it directly.

## Consequences

- Directive validation is a **runner-level** concern, not a rule. This sets the
  precedent for the future "useless suppression" detector (#33), which will reuse
  this same code-less channel rather than introducing a self-referential rule.
- Because a `DirectiveError` has no code, it cannot be `ignore`d or suppressed —
  correct: there is no coherent way to silence "your silencing directive is
  broken."
- `tests/lintrun.py`, which parses stdout back into violations, must learn to
  separate `DirectiveError` lines (post-location text starting `invalid garuff
  directive:`) from violation locators so `codes`/`violations` stay clean.
- Only two cases are reported here. A directive naming a real-but-project-scope
  code, or a real-but-globally-`ignore`d code, is a *silent no-op* for now (it
  names a known code, so it is not "unknown"); reporting those as useless is
  deferred to #33.
