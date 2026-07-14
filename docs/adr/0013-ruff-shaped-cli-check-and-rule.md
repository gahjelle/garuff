# A ruff-shaped CLI: `check` and `rule`, no default command

#6 needs a second command (`explain <CODE>`). argparse has no native "default
subcommand", so keeping bare `garuff <paths>` working alongside `garuff explain`
requires peeking at `argv[0]` before parsing. garuff ships beside ruff in every
project's dev dependencies, and agents already have `ruff check` in their
fingers. There are no users yet, so the CLI is still free to move.

## Decision

Mirror ruff. `garuff check [paths]` lints (no paths → the project root,
preserving #31); `garuff rule <CODE>|--all` explains. Bare `garuff` prints help
and exits **2**, as bare `ruff` does. The subcommand is named **`rule`**, not the
issue's `explain`, for the same reason.

We accept that `check` **collides with the glossary**: `CONTEXT.md` defines a
Check as *one rule applied to one input*, while `garuff check` names a whole run.
The two registers are documented rather than reconciled — the CLI speaks the
ecosystem's language, the domain model keeps its precision. Renaming the domain
term to protect a CLI word would be churn in the wrong direction.

## Consequences

- `justfile`'s `uv run garuff` → `uv run garuff check`; the `lint` test fixture
  prepends the word, so no rule test changes.
- Room for `garuff config` / `garuff linter` later without re-litigating dispatch.
- Real subparsers means `garuff --help` lists the commands.
