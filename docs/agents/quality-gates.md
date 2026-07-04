# Quality gates

`just check` is the **definition of done** for every slice. It runs the gates in order, stopping on the first failure:

1. `just fmt-check` — `uv run ruff format --check`
2. `just lint` — `uv run ruff check`
3. `just typecheck` — `uv run ty check` (covers `src/` and `tests/`)
4. `just test` — `uv run pytest -q`

A slice is not done until `just check` is green. CI mirrors these exact commands on every push and pull request, so a green CI means the same gate passed remotely.

There is deliberately **no `conventions` gate yet.** garuff's whole purpose is to *be* the convention linter (the `GAC`/`GAA` rules; see `docs/structure-plan.md`), so bootstrapping with a rival linter would just create a second vocabulary to tear out later. Once garuff can lint its own `src/`, it self-hosts and this gate grows a fifth step.

## Quick fixes

- Auto-format: `just fmt`
- Lint fix: `just fix` (runs `ruff check --fix`, then `ruff format`)

## Pre-commit hooks

Run `uv run prek install` once after cloning to wire up git pre-commit hooks. The hooks run ruff lint, ruff format, and ty on every commit — catching those failures before they reach CI. (The `test` gate runs in `just check` and CI, not on every commit.) Run the hooks across the whole tree at any time with `just hooks` (`uv run prek run --all-files`).
