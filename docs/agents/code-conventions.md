# Code conventions

## Environment

- Python 3.14, managed by **uv**.
- Install deps: `uv sync`. Run tools: `uv run <tool>`.
- Source layout: `src/garuff/` for application code, `tests/` for tests.
- **Zero runtime dependencies** — garuff is a linter installed into every project's dev and CI environment, so it uses only the standard library at runtime (config parsed with `tomllib`, validated by hand). See [ADR-0002](../adr/0002-zero-runtime-dependencies.md). New features must justify any dependency against this constraint; the default answer is "use the standard library."

## Package layout

garuff follows the structure settled in [`docs/structure-plan.md`](../structure-plan.md) — a thin CLI over a rule pipeline:

- `cli.py` — thin layer: argparse dispatch (default lint command + `explain`), exit codes. No domain logic.
- `rule.py` — the `SourceRule` / `TextRule` / `ProjectRule` bases (one per scope).
- `registry.py` — explicit aggregation of every rule; lookup by code.
- `config.py` — project discovery + strict `[tool.garuff]` parsing/validation.
- `files.py` — the filesystem seam `config` and `runner` share: gathering
  lintable files and matching `per-file-ignores` globs (`PerFileIgnore`).
- `suppression.py` — parse `# garuff: ignore[...]` directives; filter violations.
- `runner.py` — orchestration of the run pipeline.
- `schemas.py` — the passive result/value types (`Location`, `Violation`, `ParseFailure`, `RunResult`); a low-dependency leaf module. See [ADR-0004](../adr/0004-passive-result-types-live-in-schemas.md).
- `output.py` — rendering of those types (terse locator lines + explain appendix).
- `rules/code/` (`GAC`) and `rules/agent/` (`GAA`) — the rules themselves.

These modules are created test-first as real work lands; this describes the intended shape, not a scaffold to fill in upfront.

## Linting and formatting

- **ruff** with `select = ["ALL"]` and ignores `COM812`, `D203`, `D213`. Unlike upstream, `PLR0913` (too-many-arguments) stays **active** as the interim positional-args guardrail until garuff self-hosts its own successor rule.
- Per-file test ignores: `S101`, `PLR2004`, `SLF001`, `INP001`.
- Full **type annotations** are required on all public APIs (ruff `ANN` rules), checked by **ty** over `src/` and `tests/`.
- Never blanket-ignore the linter with `# noqa` — fix the issue or use a targeted `# noqa: CODE` with a comment explaining why.
- For intentional Unicode that trips RUF001 (ambiguous characters), use `\N{name}` escapes (e.g. `\N{EN DASH}`), not the literal or a `\u` escape.

## Conventions garuff's own code follows

garuff's coding conventions *are its own product* — the `GAC`/`GAA` rules it will one day enforce on itself (dogfooding). Until it self-hosts, follow them by hand:

- No `from __future__ import annotations` — 3.14 evaluates annotations lazily (PEP 649), so the import is dead weight.
- Docstrings use **single** backticks, never double.
- **Every** `def`/`async def` has at least a one-line docstring — including `_`-prefixed helpers and nested functions, which ruff's `D` rules leave alone.
- `@dataclass(kw_only=True)` — never let value objects be built positionally.
- Homogeneous sequences use `list[T]`, not `tuple[T, ...]`.
- Return `Self`, not a string forward-ref to the enclosing class.
- At most **1 positional parameter** — make the rest keyword-only (after a bare `*`).
- `Protocol` methods omit the `...` body — the docstring is body enough.
- No possessive `my` prefix (`my_`, `my-`, `My<Upper>`) in code or docs.

The **authoritative catalog** of these rules — codes, scopes, exact semantics, and the old `WNG` originals they descend from — lives in [`docs/structure-plan.md`](../structure-plan.md), `CONTEXT.md`, and the tracer issues. Don't restate rule semantics here; that's the one place they're defined.

## Style

- **Always read text with `encoding="utf-8"`.** `Path.read_text()` and `open()` default to the platform's *locale* encoding, which on Windows is not UTF-8 and varies machine to machine — a latent portability bug. garuff assumes every file it lints, Python and Markdown alike, is UTF-8; pass `encoding="utf-8"` explicitly on every text read. (A future GAC rule flagging encoding-less reads is a natural candidate.)
- Prefer `pathlib` over `os.path` for filesystem operations.
- Keep the `cli` layer thin — application logic lives in domain modules, not CLI handlers.
- Avoid underscore-prefixed names for "private" symbols — the visual noise outweighs the benefit. Control the public API with `__all__` when a module needs to distinguish exported names from internal helpers.

## Domain vocabulary

Vocabulary comes from `CONTEXT.md`. Do not invent synonyms. If you introduce a genuinely new domain term, update `CONTEXT.md` first.
