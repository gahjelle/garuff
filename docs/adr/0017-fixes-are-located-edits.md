# Fixes are located Edits, gated by suppression and applied in one pass

`garuff check --fix` must apply safe textual repairs and then report only what
remains, while honouring `ignore`, `per-file-ignores`, and inline suppression —
a suppressed occurrence is neither reported nor fixed. garuff is agent-facing, so
a fragile or wrong fix costs more than the tokens it saves: the standing policy
is that fixers are reserved for *safe, mechanical, single-site* repairs, and
anything that breaks callers or needs a coordinated edit elsewhere is left to the
agent.

## The rejected alternative

The most powerful shape is a whole-text `fix(text) -> new_text` per rule. It is
rejected because it cannot skip a *single* suppressed occurrence without being
handed the suppressed ranges and trusted to honour them — which pushes
suppression logic into every fixer. Its one real advantage, coordinated
multi-site edits, is needed *only* by the fixes we decline anyway: GAC006 would
add a `Self` import, GAC007 moves an import, GAC005 would leave the annotation
lying about a still-`tuple` value, and GAC008/GAC009 break call sites. So we give
up whole-text power until a *safe* multi-site fixer genuinely needs it, and
revisit this ADR then.

## The decision

A fixable rule carries an optional fixer that mirrors its `check`: it walks the
same input through the same shared detection predicate — so the two cannot drift
about what a violation is — and yields one located `Edit` per occurrence. An
`Edit` is a single half-open range `[start, end)` plus its `replacement`, tagged
with the occurrence's `Location` and the `original` slice it expects (a guard).

The shared predicate is one-directional: a fixer's *emitting* predicate may be a
strict subset of `check`'s *detecting* predicate, never a superset. A fixer may
decline to repair a genuine violation behind an extra guard — GAC003's `edits`
skips a `...` whose method has no docstring, because deleting the sole body
statement would leave an empty suite (`SyntaxError`); `check` still reports it,
it is simply not auto-fixable. What a fixer must never do is emit an `Edit` for
something `check` would not flag. So "cannot drift" means the fixer never invents
a violation, not that it must fix every one it shares.
Edits are gated by the same suppression/ignore machinery as the violations they
would have reported, reused unchanged (`config.active`, `per-file-ignores`,
`Suppressions`).

The fixer method is named `edits`, not `fix`. `Rule` already has a `fix` *field*
— the prose correct-form part of the Explanation (see ADR-0014) — and because
`Rule` is a dataclass, that instance attribute would shadow any same-named
method, making the fixability signal impossible to read. `edits` keeps the two
distinct: the noun `Edit` for what a fixer produces, the prose `fix` for what the
Explanation tells a reader.

`--fix` is a single fix-then-recheck pass per file — no iterate-to-fixpoint,
which the three shipped fixers do not need (deleting a future import or a `...`,
or collapsing backticks, never regenerates the violation). Collect the active,
non-ignored fixers' Edits, drop the suppressed ones, apply the survivors
high-offset-first (skipping overlaps and `original` mismatches so earlier offsets
never shift), verify the result still parses, write back only if it changed and
is valid, then run the normal check over the fixed text. A parse-after-fix safety
net discards all fixes for a file whose rewrite no longer parses, so a buggy
fixer never leaves a file broken on disk.

## Consequences

Suppression reuses the existing machinery with only a small `suppresses_code`
twin added for the Edit side. The apply layer (`fixes.apply_edits`) is trivial
and order-independent. The fixable set is intentionally small — GAC001, GAC003
(guarded so it never strips a method's sole body line), GAC004 — and grows one
rule at a time. The design is forward-compatible with a future `Edit`-list for
safe multi-site fixes without touching the apply logic. The summary gains a
symmetrical fixes clause under `--fix` only; the exit code is computed on the
post-fix remainder, so a fully-fixed run exits `0`.
