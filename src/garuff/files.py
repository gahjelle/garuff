"""Filesystem seam — gathering lintable files and matching per-file globs.

Both `config` (validating suppression globs against the whole project) and
`runner` (selecting which rules a file skips) need to walk the tree and match a
root-relative POSIX path against a glob. That shared machinery lives here so
neither module owns it and config need not reach into runner (see ADR-0008).
"""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# The file extensions garuff lints. Source rules run on `.py` only; text rules
# run on the raw text of every gathered file.
LINTED_SUFFIXES = frozenset({".py", ".md"})


def gather_files(*, paths: list[Path]) -> list[Path]:
    """Collect the linted files under the given paths, de-duplicated and sorted."""
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(
                found
                for found in path.rglob("*")
                if found.suffix in LINTED_SUFFIXES and found.is_file()
            )
        elif path.suffix in LINTED_SUFFIXES:
            files.add(path)
    return sorted(files)


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
