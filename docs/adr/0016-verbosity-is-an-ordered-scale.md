# Verbosity is an ordered scale; `-q` ships summary-only

`garuff check` always wrote its one-line run summary to stderr, so a clean run
was never silent — visible in garuff's own `justfile`, where every other gate is
quieted and garuff was the odd one out. We add `-q`/`--quiet` to turn that
output down, modelling verbosity as an **ordered scale** — `Verbosity(QUIET <
DEFAULT)`, an `IntEnum` in `output.py` — even though only one level ships now.

`-q` changes what is **printed**, never what is **returned**: exit codes are
untouched.

## What `-q` suppresses

`-q` drops **exactly** the run summary, on clean **and** dirty runs alike. The
per-violation count is chatter — the locator lines already carry every
violation, and the exit code already carries the pass/fail signal.

Everything else survives: findings and the appendix (stdout), parse failures,
config/path errors (exit 2), and the git-scope warning (`NO_GIT_WARNING`). The
dividing line is **quiet suppresses *status*; the future silent suppresses
*diagnostics*.** The git-scope warning is a diagnostic — it means results were
computed under degraded exclusion — not chatter, so it stays under `-q`.

## Considered options

- **A boolean `quiet` flag.** Rejected: the moment a second level lands
  (`-s`/`-v`, #42) a bool has to become a scale anyway, re-touching every gate.
  An ordered enum lets each gate read as a threshold (`verbosity >=
  Verbosity.DEFAULT`), so adding `SILENT` below or `VERBOSE` above is a
  non-breaking extension the call sites already read correctly for. The enum
  reserves both ends and ships no dead members.
- **Ship all four levels now.** Rejected: only `-q` has a proven need. `-s`/`-v`
  are *not* wired — no stub flags in `--help` — and are tracked in #42.
- **A `[tool.garuff]` config knob.** Rejected: verbosity is a property of the
  *invocation*, not the project. A config key would be the first non-rule setting
  and would blur `CONTEXT.md`'s "Configuration addresses rules by code only." So
  verbosity is flag-only.
- **A global flag.** Rejected: `-q` is `check`-scoped, mirroring `ruff check -q`.
  `rule` has no status output to quiet, so a global no-op flag was rejected.

## Consequences

- The enum lives in `output.py` (rendering-policy vocabulary), not `cli.py`:
  the dependency direction stays `cli → output`, and `output.py` must own the
  enum anyway once `-s` needs the render layer to drop findings. `render_summary`
  stays a pure string builder; `cli.py` wraps only its *write* in the threshold.
- `check(*, paths, verbosity)` takes no default — `main` always supplies it,
  keeping the seam explicit.
- The `dogfood` recipe now runs `garuff check -q`, so a clean project root is
  silent like the other gates.
- #42 fills in `-s`/`--silent` and `-v`/`--verbose` at the reserved ends.
