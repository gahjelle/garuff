# Quality gates

`just check` is the **definition of done** for every slice. It runs the gates in order, stopping on the first failure:

1. `just fmt-check` — `uv run ruff format --check`
2. `just lint` — `uv run ruff check`
3. `just typecheck` — `uv run ty check` (covers `src/` and `tests/`)
4. `just dogfood` — `uv run garuff check -q` (garuff lints its own project root)
5. `just test` — `uv run pytest -q`
6. `just audit-workflows` — `uv run zizmor .github/workflows` (workflow security)

A slice is not done until `just check` is green. CI mirrors these exact commands on every push and pull request, so a green CI means the same gate passed remotely.

garuff **self-hosts** — the `dogfood` gate runs garuff's own `GAC`/`GAA` rules (see `docs/structure-plan.md`) over the repo, which is why there is no separate rival-linter `conventions` gate. As rules land, `dogfood` enforces more of garuff's conventions automatically.

Two release-related recipes are **not** part of `check` and are run by hand, not by CI:

- `just pin` — `uv run gha-update`, re-pins every workflow `uses:` to a commit SHA. Run it after editing a workflow.
- `just release` — `uv run bumpver update`, cuts a CalVer release (bump, re-lock, commit, tag, push). See [ADR-0019](../adr/0019-calver-via-bumpver.md).

## Quick fixes

- Auto-format: `just fmt`
- Lint fix: `just fix` (runs `ruff check --fix`, then `ruff format`)

## Pre-commit hooks

Run `uv run prek install` once after cloning to wire up git pre-commit hooks. The hooks run ruff lint, ruff format, and ty on every commit — catching those failures before they reach CI. (The `test` gate runs in `just check` and CI, not on every commit.) Run the hooks across the whole tree at any time with `just hooks` (`uv run prek run --all-files`).
