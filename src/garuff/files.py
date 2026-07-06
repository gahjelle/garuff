"""Filesystem seam — gathering lintable files and matching per-file globs.

Both `config` (validating suppression globs against the whole project) and
`runner` (selecting which rules a file skips) need to walk the tree and match a
root-relative POSIX path against a glob. That shared machinery lives here so
neither module owns it and config need not reach into runner (see ADR-0008).

File selection also excludes third-party / generated trees in two layers, both
resolved here: dot-prefixed directories are always skipped, and — inside a git
work-tree — the walk is intersected with git's view of the tree, carried as a
`GitScope`. `discover_git_scope` is the one site that shells out to git and
decides the no-git fallback, so `gather_files` stays pure (see ADR-0009).
"""

import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "GitScope",
    "PerFileIgnore",
    "discover_git_scope",
    "gather_files",
    "relative_posix",
]

# The file extensions garuff lints. Source rules run on `.py` only; text rules
# run on the raw text of every gathered file.
LINTED_SUFFIXES = frozenset({".py", ".md"})

# Emitted once when git can't answer, so the user knows exclusion is degraded.
NO_GIT_WARNING = (
    "warning: not a git repository (or git unavailable) — "
    "gitignore-based file exclusion is off; only hidden directories are skipped\n"
)


@dataclass(frozen=True)
class GitScope:
    """Git's view of which files under a root belong to the work-tree.

    `allowed` is the set of absolute paths git tracks or leaves un-ignored, or
    None when the root is not in a git work-tree or git is unavailable. An
    *empty* set — git ran over an all-ignored tree — still means "lint nothing"
    and is deliberately distinct from the None sentinel, which means "no git, so
    apply no intersection at all." Wrapping the sentinel in a typed value keeps
    that distinction explicit wherever the scope is threaded.
    """

    allowed: frozenset[Path] | None

    @property
    def available(self) -> bool:
        """Whether a git work-tree answered, so the git intersection applies."""
        return self.allowed is not None

    def permits(self, file: Path) -> bool:
        """Whether file survives the git intersection (always True with no git)."""
        return self.allowed is None or file.resolve() in self.allowed


def discover_git_scope(
    root: Path, *, warn: Callable[[str], object] | None = None
) -> GitScope:
    """Query git once for the work-tree under root; warn if git can't answer.

    The single site that shells out to git and owns the no-git fallback: when
    there is no work-tree (or no git binary) and a `warn` sink is supplied, it
    emits `NO_GIT_WARNING` there exactly once. The returned scope is threaded
    into `load` and `run`, leaving `gather_files` free of subprocess and IO.
    """
    scope = GitScope(allowed=git_lintable(root))
    if warn is not None and not scope.available:
        warn(NO_GIT_WARNING)
    return scope


def git_lintable(root: Path) -> frozenset[Path] | None:
    """Absolute paths git considers part of the work-tree at root, or None.

    Returns the tracked plus untracked-but-not-ignored files — git honours every
    `.gitignore`, `.git/info/exclude`, and global exclude, so we parse none of it
    ourselves. Returns None when root is not inside a git work-tree or the git
    binary is unavailable. An empty frozenset (git ran over an empty/all-ignored
    tree) is distinct from None and is honoured as "lint nothing".
    """
    if shutil.which("git") is None:
        return None
    # `root` stays its own argument: interpolating it into a shlex string would
    # split a path that contains spaces into separate tokens and break `-C`.
    flags = shlex.split("ls-files --cached --others --exclude-standard -z")
    command = ["git", "-C", str(root), *flags]
    try:
        completed = subprocess.run(command, capture_output=True, check=True)  # noqa: S603
    except subprocess.CalledProcessError, FileNotFoundError, OSError:
        return None
    # -z gives NUL-separated, unquoted paths. Keep stdout as bytes and decode
    # with surrogateescape so a non-UTF-8 filename round-trips instead of raising
    # UnicodeDecodeError (which `text=True` would, escaping the fallback).
    names = [
        chunk.decode("utf-8", "surrogateescape")
        for chunk in completed.stdout.split(b"\0")
        if chunk
    ]
    return frozenset((root / name).resolve() for name in names)


def gather_files(*, paths: list[Path], scope: GitScope) -> list[Path]:
    """Collect the linted files under the given paths, de-duplicated and sorted.

    Two exclusion layers apply during directory traversal — never to an
    explicitly named file:
      * dot-dir skip — any file with a dot-prefixed path component below the
        walked directory is skipped (catches `.venv`, `.git`, caches, and the
        tracked `.claude`/`.github` trees);
      * git intersection — when `scope` comes from a git work-tree, only files it
        permits survive (its view excludes gitignored trees like `build/`).
        Outside a work-tree the scope permits everything; dot-dir skipping still
        runs.
    """
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            for found in path.rglob("*"):
                if found.suffix not in LINTED_SUFFIXES or not found.is_file():
                    continue
                if has_dot_component(found, root=path):
                    continue
                if not scope.permits(found):
                    continue
                files.add(found)
        elif path.suffix in LINTED_SUFFIXES:
            files.add(path)
    return sorted(files)


def has_dot_component(file: Path, *, root: Path) -> bool:
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
