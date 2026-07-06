"""Filesystem seam — gathering lintable files and matching per-file globs.

Both `config` (validating suppression globs against the whole project) and
`runner` (selecting which rules a file skips) need to walk the tree and match a
root-relative POSIX path against a glob. That shared machinery lives here so
neither module owns it and config need not reach into runner (see ADR-0008).
"""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# The file extensions garuff lints. Source rules run on `.py` only; text rules
# run on the raw text of every gathered file.
LINTED_SUFFIXES = frozenset({".py", ".md"})


def git_lintable(root: Path) -> frozenset[Path] | None:
    """Absolute paths git considers part of the work-tree at root, or None.

    Returns the tracked plus untracked-but-not-ignored files — git honours every
    `.gitignore`, `.git/info/exclude`, and global exclude, so we parse none of it
    ourselves. Returns None when root is not inside a git work-tree or the git
    binary is unavailable; the caller then falls back to dot-dir skipping alone
    and warns. An empty frozenset (git ran over an empty/all-ignored tree) is
    distinct from None (no git) and is honoured as "lint nothing".
    """
    if shutil.which("git") is None:
        return None
    command = [
        "git",
        "-C",
        str(root),
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    try:
        completed = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError, FileNotFoundError, OSError:
        return None
    # -z yields NUL-separated, unquoted paths (robust to spaces/newlines/unicode);
    # split on NUL and drop the trailing empty. Paths are relative to root.
    names = [name for name in completed.stdout.split("\0") if name]
    return frozenset((root / name).resolve() for name in names)


def gather_files(
    *, paths: list[Path], allowed: frozenset[Path] | None = None
) -> list[Path]:
    """Collect the linted files under the given paths, de-duplicated and sorted.

    Two exclusion layers apply during directory traversal — never to an
    explicitly named file:
      * dot-dir skip — any file with a dot-prefixed path component below the
        walked directory is skipped (catches `.venv`, `.git`, caches, and the
        tracked `.claude`/`.github` trees);
      * git intersection — when `allowed` is not None, only its members survive
        (git's view of the work-tree, so gitignored trees like `build/` drop
        out). `allowed` is None when there is no git work-tree; dot-dir
        skipping still runs.
    """
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            for found in path.rglob("*"):
                if found.suffix not in LINTED_SUFFIXES or not found.is_file():
                    continue
                if _has_dot_component(found, root=path):
                    continue
                if allowed is not None and found.resolve() not in allowed:
                    continue
                files.add(found)
        elif path.suffix in LINTED_SUFFIXES:
            files.add(path)
    return sorted(files)


def _has_dot_component(file: Path, *, root: Path) -> bool:
    """Report whether any directory component of file below root starts with a dot.

    Keys on the components between root and the filename (`parts[:-1]`), so a
    directory named on the command line is walked even if it is itself
    dot-prefixed — only its dot-prefixed descendants are pruned.
    """
    return any(part.startswith(".") for part in file.relative_to(root).parts[:-1])


def relative_posix(file: Path, *, root: Path) -> PurePosixPath:
    """Return file as a root-relative POSIX path, ready for glob matching.

    Anchoring to root and normalising to POSIX means `**` crosses directory
    segments and globs match the same way on every platform.
    """
    return PurePosixPath(file.relative_to(root).as_posix())


@dataclass(kw_only=True)
class PerFileIgnore:
    """One `per-file-ignores` entry: a glob and the rule codes it silences."""

    glob: str
    codes: frozenset[str]

    def matches(self, file: Path, *, root: Path) -> bool:
        """Report whether file (anchored at root) is matched by this entry's glob."""
        return relative_posix(file, root=root).full_match(self.glob)
