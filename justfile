default: check

# Run all quality gates in order, stopping on the first failure.
check: fmt-check lint typecheck dogfood test audit-workflows

# Check formatting without writing changes.
fmt-check:
    uv run ruff format --check -q

# Lint the codebase with ruff.
lint:
    uv run ruff check -q

# Type-check src/ and tests/ with ty.
typecheck:
    uv run ty check -q

# Lint garuff's whole project root with garuff (the default scope).
dogfood:
    uv run garuff check -q

# Run the test suite quietly.
test *args:
    uv run pytest -q {{args}}

# Audit the GitHub Actions workflows for security issues with zizmor.
audit-workflows:
    uv run zizmor .github/workflows -q

# Pin every workflow `uses:` to a commit SHA with gha-update.
pin-workflows:
    uv run gha-update

# Cut a release: bump the CalVer version, re-lock, commit, tag, and push.
release *args:
    uv run bumpver update {{args}}

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
