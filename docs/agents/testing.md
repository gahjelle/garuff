# Testing

## Approach

Work test-first: defer to the `tdd` skill for the red → green → refactor loop. Write a failing test before any implementation, then make it pass with the minimum code needed.

## What to test

- Assert **external behavior via the CLI** — invoke `main()` (or `garuff [paths...]`) end-to-end and assert on what a user observes.
- The **exit code is a behavior contract** worth asserting directly: `0` clean, `1` violations found, `2` config error (see `CONTEXT.md` and `docs/structure-plan.md`).
- A rule's job is to flag the right **violation** at the right location: assert the `CODE` and the `path:line:col` it reports, not the rule's internals.
- Do not test implementation details; test observable outcomes.

## Fixture projects under `tmp_path`

garuff runs *inside a target project* — it discovers a root by walking up to the nearest `pyproject.toml`, then lints from there. So tests build a **throwaway project** on disk and point garuff at it:

- Use `tmp_path` (pytest's built-in fixture) — the only real filesystem boundary allowed in tests — to lay down a `pyproject.toml` plus the sample `.py` / `.md` files a case needs.
- Drive `main()` against that directory and assert on the reported violations and exit code.
- No mocking of the filesystem — use `tmp_path` for real file I/O. No network calls in tests.
- Test functions and helpers obey **GAC008** (at most one positional parameter) like the rest of the codebase — there is no `tests/` exemption. Put fixtures after a bare `*` (`def test_x(*, tmp_path, monkeypatch)`); pytest injects them by keyword, so keyword-only parameters receive their fixtures normally (this holds for `@parametrize` args and fixture-of-fixtures too). Helpers with a natural positional subject keep it and push the rest behind `*` (`def build_tree(root, *, files)`).

A test for a single rule is a minimal fixture project containing exactly the code that should (or shouldn't) trip it.

## Dogfood

garuff should pass its own rules. As rules land, a test that runs garuff against garuff's **own `src/`** and asserts a clean (or intended-only) result guards against the linter regressing on the very conventions it enforces. Several tracer issues call for this dogfood check explicitly.

## Test layout

Tests live in `tests/`. Pytest is configured with `testpaths = ["tests"]` and the src layout (`src/` on the path via uv). Test files follow the `test_<module>.py` convention.
