# CalVer `YYYY.MM.PATCH`, single-sourced and re-locked by a bumpver hook

garuff needs a version scheme and a mechanism to advance it. The version lives in
`pyproject.toml [project].version` (read by the `uv_build` backend) and is
permanent once published to PyPI, so the choice is load-bearing.

## The scheme

CalVer `YYYY.MM.PATCH` — non-padded month (May is `5`, not `05`) — advanced with
[`bumpver`](https://github.com/mbarkhau/bumpver). Releases here are date-driven,
not API-contract-driven, so SemVer would promise a compatibility contract garuff
does not reason about. Within a month the `PATCH` counts releases; when the month
rolls over, `bumpver` resets `PATCH` to `0`.

The version is single-sourced in `pyproject.toml`. `bumpver update` rewrites the
static string; `just release` wraps it, and bumpver then commits, tags, and
pushes.

## The `v`-prefix lives only in the tag

The release trigger is a `v`-prefixed tag (`v2026.7.0`), but `[project].version`
must stay a bare PEP 440 string (`2026.7.0`). bumpver ties the tag name to the
version string, so the `v` is carried in bumpver's own `version_pattern`
(`vYYYY.MM.PATCH`) and `current_version` (`v2026.6.0`). The tag and bumpver's
bookkeeping are `v`-prefixed; the `[project].version` file pattern uses the
`{pep440_version}` token, which normalises the `v` away, so the published version
stays bare. One config, both forms, no drift.

## The lockfile rides in the bump commit

`bumpver`'s `pre_commit_hook` runs `.pre-commit-bumpver.sh`, a two-line
`/bin/sh` script that does `uv lock` + `git add uv.lock`. So **uv itself**
recomputes the lockfile into the same commit that bumps the version, and
`pyproject.toml` and `uv.lock` stay consistent by construction.

## Rejected alternatives

- **SemVer** — rejected: the release cadence is date-driven; a
  `MAJOR.MINOR.PATCH` contract would over-promise.
- **VCS / dynamic versioning** (deriving the version from the tag at build time)
  — rejected: bumpver's model is rewriting a static string, and switching to a
  dynamic backend is a larger change than this needs.
- **bumpver string-patching `uv.lock` via `file_patterns`** — rejected:
  `uv.lock` has a `version` line *per package*, so a naive string match risks
  rewriting the wrong entry, and the lock format is uv's to own, not ours to
  pattern-match. Letting `uv lock` regenerate it is correct by construction.

## Consequences

- The first release seeds `current_version = "v2026.6.0"`, so the first
  `just release` (run in July 2026) produces `2026.7.0` — the intended first
  published version — via the ordinary month-rollover path, no special-casing.
- The tag `v2026.7.0` is the single release trigger
  (see [ADR-0018](./0018-single-gated-release-workflow.md)).
- The cost is one committed `/bin/sh` hook script and a dev dependency on
  `bumpver`.
