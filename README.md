# garuff

**Personal, opinionated Python linter rules aimed at coding agents.**

garuff enforces a curated set of conventions that [ruff](https://docs.astral.sh/ruff/)
and [ty](https://github.com/astral-sh/ty) can't express — and it explains every
one of them in terms a coding assistant can act on.

> ⚠️ **Early days.** The core linter runs — `garuff check` and `garuff rule`
> work today — but the ruleset is still small and there's no packaged release
> yet. This README describes the vision; the full rule reference and install
> instructions will land as the implementation does.

## Why

Coding agents write a lot of code, fast. Keeping that code consistent means
enforcing conventions — but enforcement alone isn't enough for an agent. A
terse `remove this` tells a human who already knows the house style exactly what
to do; an agent needs to know *why* the convention exists, or it will "fix" the
symptom and reintroduce the cause a moment later.

ruff and ty are indispensable, and garuff is not a replacement for either. It
fills the gap they leave:

- **Conventions they can't express.** Repo-specific taste — "return `Self`, never
  a stringized forward reference to the enclosing class", "every function carries
  a docstring", "keep agent-facing docs like ADRs consistently numbered."
- **Messages written for agents.** Every rule ships a *rationale* (why the
  convention exists) and a *prescribed fix* (the correct form), not just a
  one-line complaint.

## What makes it different

- **Agent-first by design.** Each violation carries a terse summary to locate it,
  a rationale to justify it, and a fix to resolve it. Output stays scannable:
  the reasoning for each triggered rule is shown once, not repeated on every hit.
- **Opinionated, not configurable-to-taste.** garuff is a point of view, not a
  style engine. The rules encode one set of preferences; you don't tune them into
  something else — you take them or turn them off.
- **Enforcement you control.** Every rule is on by default. You can ignore
  individual rules, silence them per file, or suppress a single line inline —
  while the ruleset itself stays fixed.
- **Zero dependencies.** garuff is a tool you install into every project's dev
  and CI environment, so it leans on nothing but the standard library and drops
  in without dependency friction.

## Using it

`garuff check [paths]` lints (no paths → the whole project root). Each violation
is a terse locator line; once all findings are listed, an **appendix** explains
each rule that fired — once, no matter how many times it tripped:

```
$ garuff check src
src/config.py:1:1: GAC001 no `from __future__ import annotations`
src/build.py:9:1: GAC008 `build` takes 3 positional parameters (at most 1)

  GAC001  no `from __future__ import annotations`
      why  Python 3.14 evaluates annotations lazily (PEP 649), so the import is
           dead weight — it buys nothing and every module has to carry it.
      fix  Delete the import:
               - from __future__ import annotations

  GAC008  keep positional parameters to at most 1
      why  Positional parameters past the first make a call site ambiguous — the
           reader has to count arguments and match them against the signature to
           know what each one means.
      fix  The limit is 1; move every parameter past it behind
           a bare `*` so callers must name them:
               def build(name, kind, size): ...     # before
               def build(name, *, kind, size): ...  # after
           ...
```

Findings go to stdout, one per line at column 0; the appendix is indented
beneath them, so `garuff check | grep '^[^ ]'` filters the findings alone.

`garuff rule <CODE>` prints that same explanation on demand — reading the
project's configuration, so a tuned option (say a raised `max-positional-args`)
shows up in the text — and `garuff rule --all` prints the whole ruleset. A rule
you've turned off still explains itself, and says that it's ignored.

## Two kinds of rules

- **Code rules** — how you write Python and its prose: types, docstrings, naming,
  model and dataclass conventions.
- **Agent-file rules** — how a repository's agent-facing scaffolding is
  structured: ADRs today, more of the agent surface over time.

## Status & direction

The domain model, the key architectural decisions, and the build plan are written
down:

- [`CONTEXT.md`](./CONTEXT.md) — the project's glossary.
- [`docs/adr/`](./docs/adr/) — the decisions and why they were made.
- [`docs/structure-plan.md`](./docs/structure-plan.md) — how the tool is put together.

Implementation is tracked as a sequence of end-to-end
[issues](https://github.com/gahjelle/garuff/issues). This page will grow into
proper documentation as those land.
