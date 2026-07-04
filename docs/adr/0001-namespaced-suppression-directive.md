# Inline suppression uses `# garuff: ignore[...]`, not `# noqa`

garuff exists to catch conventions ruff and ty cannot express, so ruff is almost
always running in the same project. We therefore give garuff its own namespaced
inline-suppression directive — `# garuff: ignore[GAC008]` — instead of reusing
flake8/ruff's `# noqa`. Codes are required; there is no bare form.

## Considered options

- **Reuse `# noqa`.** Rejected: the two linters would fight over one comment.
  ruff's unused-noqa rule (`RUF100`) does not recognise garuff's codes, so it
  would flag every garuff suppression as a useless noqa and try to delete it.
  A bare `# noqa` would also silence ruff and garuff together, making it
  impossible to suppress one without the other.
- **Namespaced `# garuff: ignore[...]` (chosen).** ruff ignores it entirely; the
  two tools never contend for the same comment.

## Consequences

- The directive is load-bearing syntax: once users write it, changing it is a
  breaking change — the same reversibility cost as the rule codes themselves.
- Suppression is only available to source-scope and Python text-scope rules.
  Project-scope rules (e.g. ADR numbering) have no line to anchor a comment to
  and can only be silenced via global `ignore` in configuration.
