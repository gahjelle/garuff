# Scratch directory

`.scratch/` (gitignored) is where architecture reviews, handoffs, and other
temporary or working documents go — anything that isn't meant to live in the
repo's tracked docs.

- Write temporary/working documents there instead of `/tmp` or the repo root.
- Files are **not** automatically deleted. The maintainer manages cleanup manually.
- **Agents must not delete anything in `.scratch/`** — not even files an agent
  itself created earlier in the session. If a file there is stale or wrong,
  leave it; don't remove it.
