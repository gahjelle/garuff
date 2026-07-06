# The empty-glob check is judged against the whole project, not the run's files

A `per-file-ignores` glob that matches no files is a config error (exit `2`), to
catch dead or typo'd entries. "No files" is judged against the **whole project**
— `gather_files([root])`, computed inside `config.load` — not against the files
gathered for the current invocation. So the check is about "is this glob dead for
the project?", independent of which paths a given run happens to lint.

## Considered options

- **Judge against the files gathered for this run.** Rejected once the
  consequence surfaced: it makes a valid config fail on a partial invocation. Once
  `"tests/**" = ["GAC008"]` exists, `garuff src/` would exit `2` because the glob
  matches nothing *this run* — so you could never lint a subset that excludes the
  ignored tree. Terrible UI for ad-hoc and agent-driven partial runs.
- **Drop the check; let dead globs pass silently.** Rejected: a typo'd glob
  (`test/**` for `tests/**`) would then silently protect nothing — precisely the
  quiet misconfiguration garuff's strictness exists to surface.
- **Whole-project universe (chosen).** Stable across invocations, reuses the
  existing `gather_files` walk, and keeps all four validation classes inside
  `config.load` as the single place `ConfigError` is raised.

## Consequences

- Partial runs never trip on globs aimed at trees they aren't linting.
- The project-file set is imprecise until file exclusion lands (#16): a walk from
  root sweeps `.venv`/vendored trees, so a junk glob that happens to match
  something there is spuriously "live." Low-risk — those files are only counted,
  never linted — and it is exactly the imprecision #16 is scoped to remove.
- Two `gather_files` passes per run: the whole-project walk for glob validation,
  and the narrower walk over the actual lint paths. Cheap and clearly separated.
- This reverses the reading implied by issue #4 (globs validated against the
  gathered set); the reversal was settled in the #4 grilling session (2026-07-06).
