default: check

# Run all quality gates in order, stopping on the first failure.
check: fmt-check lint typecheck dogfood test

# Check formatting without writing changes.
fmt-check:
    uv run ruff format --check -q

# Lint the codebase with ruff.
lint:
    uv run ruff check -q

# Type-check src/ and tests/ with ty.
typecheck:
    uv run ty check -q

# Dogfood: lint garuff's own source with garuff.
# Scoped to src/ (not tests/): the text-scope rules (e.g. GAC011) would flag the
# intentional bad-pattern examples in test fixtures, which per-file-ignores will
# exempt once config lands (#4). Matches tests/test_dogfood.py.
dogfood:
    uv run garuff src

# Run the test suite quietly.
test *args:
    uv run pytest -q {{args}}

# Auto-format the codebase with ruff.
fmt:
    uv run ruff format

# Auto-fix lint issues then reformat.
fix:
    uv run ruff check --fix -q
    uv run ruff format -q

# Run the prek pre-commit hooks against all files.
hooks:
    uv run prek run --all-files
