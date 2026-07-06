# File exclusion delegates to git; hidden directories skip by convention

When garuff walks a directory it must not lint third-party, generated, or tooling
trees (`.venv`, `build/`, `.claude/`, …). File selection is **two
convention-based layers**, both automatic and neither configurable (config knobs
are deferred to #28):

- **Layer 1 — dot-dir skip.** Always on, no git, pure. During traversal, skip any
  file with a dot-prefixed path component below the walked directory. "Starts with
  a dot" is a filesystem convention, not a maintained list, so it catches `.venv`,
  `.git`, `.mypy_cache`, and the tracked `.claude`/`.github` trees alike.
- **Layer 2 — git intersection.** When inside a git work-tree, intersect the
  gathered set with `git ls-files --cached --others --exclude-standard -z` — the
  tracked plus untracked-but-not-ignored files. This adds the *non-dot* gitignored
  trees (`build/`, `dist/`, `node_modules/`, project-specific generated dirs) that
  convention alone cannot know. Delegating to git means garuff parses no
  `.gitignore` and therefore misses none of its edge cases (negation, nesting,
  `.git/info/exclude`, global excludes, a repo-root `.gitignore` above a nested
  project root — git handles them all).

Outside a git work-tree, or when the `git` binary is absent, Layer 2 is skipped,
garuff warns once, and Layer 1 still applies. A single domain function,
`discover_git_scope`, runs the query once per run and owns the no-git warning
(emitted through an injected sink so it holds no reference to stderr). It returns
a `GitScope` value that names the sentinel distinction — an empty allow-set is
"lint nothing", `None` is "no git, apply no intersection" — and that scope is
threaded through `config.load` and `runner.run`. `cli.main` only wires the
stderr sink; `gather_files` stays a pure function with no subprocess and no IO.

## Considered options

- **Hand-rolled `.gitignore` matcher.** Rejected: it owns every one of the edge
  cases above and is exactly the "half-measure bolted onto the runner" issue #16
  warned against.
- **An `exclude` config key.** Rejected for now: it duplicates `.gitignore` by
  hand and reintroduces the maintained directory list the maintainer explicitly
  wanted to avoid. Deferred as #28.
- **git subprocess (chosen).** Makes `.gitignore` the literal source of truth,
  needs no config, and is *faster* — git prunes ignored trees during its own scan
  instead of us walking `.venv` and discarding it afterward. It stays stdlib-only
  (a system `git` binary is not a Python package dependency), so ADR-0002 holds.

## Consequences

- The git dependency is *soft*: no work-tree or no binary degrades to Layer 1 and
  warns, never a hard failure. The `GitScope` value carries this: an empty
  allow-set (git ran over an empty or all-ignored tree) is honoured as "lint
  nothing" and is distinct from the `None` sentinel (no git). A non-UTF-8 filename
  from `git ls-files -z` round-trips via `surrogateescape` rather than crashing.
- Untracked-but-not-ignored files are linted, so a brand-new uncommitted file is
  caught immediately; gitignored files never are.
- Explicit file paths bypass exclusion — the two layers apply to directory
  traversal only. Naming a dot-dir walks it, but its dot-prefixed descendants stay
  pruned.
- The whole-project glob-liveness walk (ADR-0008) now shares these exclusions,
  which removes the imprecision that ADR recorded as pending this issue.
