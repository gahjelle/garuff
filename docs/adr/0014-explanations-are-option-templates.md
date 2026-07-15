# Explanations are option templates, substituted at render time

GAC008's ceiling is configurable (`max-positional-args`, ADR-0007). Its
violation lines already report the *configured* limit via `Violation.detail`, but
a static `summary` ("at most one positional parameter") would contradict them the
moment a project sets the knob to 3 — and `garuff rule GAC008` would state a
policy the linter is not enforcing. An explanation that lies is worse than no
explanation, because an agent will act on it.

## Decision

`summary` / `rationale` / `fix` are **`string.Template` templates**, rendered by
`Rule.explanation` with the rule's own (config-baked) option values substituted
in, at **render time** — after `config.load` has done its baking.
`safe_substitute`, so an unresolvable placeholder prints verbatim instead of
raising inside a user's lint run; a registry-wide test asserts no `$` survives.

Rejected:

- **`str.format`** — `{}` is the interpolation marker, but braces are everywhere
  in a `fix` code block (dict literals, sets, f-strings). Every one would need
  doubling forever, and a missed one raises during someone's lint run.
- **t-strings (PEP 750)** — *eager*: interpolations are evaluated where the
  t-string is written, so a rule built at import time would freeze the
  **default** option value into its own explanation — precisely the bug this ADR
  exists to prevent. They also inherit f-string brace syntax (a dict literal is
  silently reparsed as an interpolation), and a `Template` is not a `str`, so
  every consumer would have to render it by hand. Making them work would require
  explanations to become methods, which every option-less rule would then
  implement to return a constant.

## Consequences

- A configurable rule must word its text to be true at **every** setting, naming
  the value (`$max_positional_args`) and never the option — an agent acting on a
  `fix` should not have to learn that configuration exists.
- Rule text is authored as plain triple-quoted strings, `cleandoc`-normalised by
  `Rule.__post_init__`; `$` is the only reserved character.
- The appendix and `garuff rule` render the *same baked rule*, so they cannot
  disagree. That — not a shared string constant — is the issue's "one source of
  truth".
