# garuff

**Personal, opinionated Python linter rules aimed at coding agents.**

garuff enforces a curated set of conventions that [ruff](https://docs.astral.sh/ruff/)
and [ty](https://github.com/astral-sh/ty) can't express — and it explains every
one of them in terms a coding assistant can act on.

> ⚠️ **Early days.** The design is settled but the tool isn't built yet. This
> README describes the vision; install instructions, the rule reference, and
> configuration details will land as the implementation does.

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
