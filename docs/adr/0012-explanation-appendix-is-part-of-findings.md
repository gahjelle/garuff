# The explanation appendix is part of the findings stream

ADR-0011 split the streams: stdout carries *findings about the code the user
wrote*, stderr carries *how the run went* (summary, parse failures, git
warning). The appendix is a new kind of output — prose, multi-line, one block
per fired rule — and it has to land on one side of that line. Putting it on
stderr would keep stdout's "one finding per line" property intact and cost
nothing today.

## Decision

The appendix goes on **stdout**, after the locator lines, on by default. It
explains findings about the user's code; it is not a report on the run.
Consequently stdout is no longer "locator lines only", and a new invariant
replaces it: **a line at column 0 is a finding; every other line is blank or
indented.** The whole appendix is indented two spaces to satisfy it.

## Consequences

- `garuff check | grep '^[^ ]'` is an exact findings filter; `tests/lintrun.py`
  parses on the same rule, and a test asserts the invariant directly.
- Verbosity is **not** this issue's business: no `--explain` flag. A clean run
  prints no appendix, so nothing needs an opt-out today, and #35 (`-q`/`-s`) owns
  the one verbosity axis.
- A future `--output-format json` serialises findings *and* their explanations
  from the same data, not by re-parsing text.
