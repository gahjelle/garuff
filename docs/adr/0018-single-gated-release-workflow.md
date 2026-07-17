# One tag-triggered release workflow, gated by a reviewed PyPI Environment

garuff publishes to PyPI from GitHub Actions. The source article the issue draws
from (<https://snarky.ca/how-to-publish-to-pypi-using-github-actions-securely/>)
suggests optionally splitting build and publish into separate workflows. We
instead use a **single** `release.yml` with three jobs — `check → build →
publish` — because the split buys complexity without buying the one thing we
actually need, which is a human pause before the irreversible upload.

## The trigger and the self-gate

`release.yml` fires only on `push: tags: ['v[0-9]*']`. There is no
`workflow_dispatch`: a release is always a pushed version tag, cut by
`just release` (see [ADR-0019](./0019-calver-via-bumpver.md)).

A tag can sit on **any** commit, so the workflow re-runs `just check` in its own
`check` job — the exact same gate CI runs on every push — before it will build
or publish. `build` `needs: check`; `publish` `needs: build`. CI therefore
cannot publish a SHA the gates have not passed, even if someone tags an arbitrary
commit.

## The review pause is a GitHub Environment

The `publish` job declares `environment: pypi`. That Environment carries a
**required-reviewer** rule, and *that rule is the "after review" pause* the issue
asks for — GitHub blocks the job until the maintainer approves it. There is no
in-workflow gate to maintain; the pause lives in repo settings where it belongs.

## The rejected alternative

Two chained workflows via `workflow_run`. Rejected because `workflow_run` runs
the **default-branch** copy of the downstream workflow (not the tagged one),
artifact passing between workflows is manual, and the review gate still has to be
a GitHub Environment regardless. The split adds moving parts without removing the
need for the Environment, so it is pure cost.

## Trusted publishing, least privilege

Publishing uses PyPI **trusted publishing** (OIDC) via
`pypa/gh-action-pypi-publish` with its default PEP 740 attestations — no
long-lived API token lives in GitHub. Top-level `permissions: {}`; each job is
granted only what it needs, and `publish` gets only `id-token: write`. Every
checkout sets `persist-credentials: false`, and every `uses:` is SHA-pinned (via
`just pin`). In the release path, `setup-uv` runs with `enable-cache: false` so a
cache poisoned by an untrusted run cannot influence a published artifact.

## Consequences

- Releasing is one command (`just release`); the pushed tag is the only trigger.
- CI cannot publish an unverified commit, and no PyPI credential is stored.
- Two one-time manual prerequisites exist outside the repo: a PyPI **pending
  publisher** for `garuff` (this repo, workflow `release.yml`, environment
  `pypi`) and the GitHub `pypi` Environment with a required reviewer. Until both
  exist, the first real tag cannot publish — the first release is the end-to-end
  test.
- Adding a manual re-run path later means adding `workflow_dispatch` with a
  version input; the single-workflow shape does not preclude it.
- Creating a GitHub Release on publish is deferred to #48; maximising zizmor
  strictness is deferred to #49.
