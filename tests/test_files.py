"""Filesystem seam — file gathering with its two exclusion layers.

`gather_files` is the pure walk: it collects lintable files under the given
paths and applies (1) dot-dir skipping always, and (2) an optional git-derived
`allowed` intersection. `git_lintable` is the impure query that produces that
`allowed` set from `git ls-files`. These tests drive both directly on
`tmp_path` trees; the git happy-path is skipped where the `git` binary is
absent, and the fallback branches are forced hermetically by monkeypatching.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from garuff.files import gather_files, git_lintable

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def build_tree(root: Path, files: list[str]) -> None:
    """Create each project-relative path under root as an empty-ish file."""
    for relpath in files:
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def git(root: Path, *args: str) -> None:
    """Run a git subcommand inside root, failing the test on error."""
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def init_repo(root: Path) -> None:
    """Init a git repo at root with deterministic identity, no signing."""
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "Test")
    git(root, "config", "commit.gpgsign", "false")


def test_gather_skips_dot_directories_at_any_depth(tmp_path: Path) -> None:
    """Files under a dot-prefixed directory are dropped, however deep."""
    build_tree(
        tmp_path,
        [
            "src/a.py",
            ".venv/lib/b.py",
            ".claude/skills/c.md",
            "pkg/.hidden/d.py",
            "pkg/e.py",
        ],
    )

    gathered = gather_files(paths=[tmp_path])

    assert gathered == sorted([tmp_path / "src/a.py", tmp_path / "pkg/e.py"])


def test_gather_intersects_with_allowed_when_given(tmp_path: Path) -> None:
    """A non-None `allowed` drops files outside it — even non-dot ones."""
    build_tree(tmp_path, ["src/a.py", "build/f.py", "pkg/e.py"])
    allowed = frozenset({(tmp_path / "src/a.py").resolve()})

    gathered = gather_files(paths=[tmp_path], allowed=allowed)

    assert gathered == [tmp_path / "src/a.py"]


def test_explicit_file_inside_dot_dir_is_linted(tmp_path: Path) -> None:
    """Naming a file directly opts it in even under a dot-prefixed directory."""
    build_tree(tmp_path, [".venv/x.py"])

    gathered = gather_files(paths=[tmp_path / ".venv/x.py"])

    assert gathered == [tmp_path / ".venv/x.py"]


def test_explicit_dot_dir_is_walked_but_nested_dot_dirs_are_pruned(
    tmp_path: Path,
) -> None:
    """Naming a dot-dir walks its plain children; deeper dot-dirs stay skipped."""
    build_tree(tmp_path, [".claude/y.md", ".claude/.git/z.md"])

    gathered = gather_files(paths=[tmp_path / ".claude"])

    assert gathered == [tmp_path / ".claude/y.md"]


def test_dot_prefixed_filename_is_not_pruned_by_layer_one(tmp_path: Path) -> None:
    """Layer 1 keys on directory components, not the filename itself."""
    build_tree(tmp_path, ["pkg/.foo.py"])

    gathered = gather_files(paths=[tmp_path])

    assert gathered == [tmp_path / "pkg/.foo.py"]


@needs_git
def test_git_lintable_reflects_tracked_and_untracked_but_not_ignored(
    tmp_path: Path,
) -> None:
    """The set holds tracked + untracked-non-ignored files, minus gitignored ones."""
    init_repo(tmp_path)
    build_tree(
        tmp_path,
        [
            ".gitignore",
            "tracked.py",
            "untracked.py",
            "ignored.py",
            "build/generated.py",
        ],
    )
    (tmp_path / ".gitignore").write_text("build/\nignored.py\n", encoding="utf-8")
    git(tmp_path, "add", ".gitignore", "tracked.py")
    git(tmp_path, "commit", "-qm", "init")

    allowed = git_lintable(tmp_path)

    assert allowed is not None
    assert (tmp_path / "tracked.py").resolve() in allowed
    assert (tmp_path / "untracked.py").resolve() in allowed
    assert (tmp_path / "ignored.py").resolve() not in allowed
    assert (tmp_path / "build/generated.py").resolve() not in allowed


@needs_git
def test_end_to_end_gather_drops_gitignored_and_dot_trees(tmp_path: Path) -> None:
    """Through gather_files, both a gitignored build/ and a .venv disappear."""
    init_repo(tmp_path)
    build_tree(
        tmp_path,
        ["src/a.py", "build/f.py", ".venv/lib/b.py", ".gitignore"],
    )
    (tmp_path / ".gitignore").write_text("build/\n.venv/\n", encoding="utf-8")
    git(tmp_path, "add", "src/a.py", ".gitignore")
    git(tmp_path, "commit", "-qm", "init")

    gathered = gather_files(paths=[tmp_path], allowed=git_lintable(tmp_path))

    assert gathered == [tmp_path / "src/a.py"]


def test_git_lintable_none_when_git_binary_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No `git` on PATH degrades to None without invoking subprocess."""
    monkeypatch.setattr("garuff.files.shutil.which", lambda _: None)

    assert git_lintable(tmp_path) is None


def test_git_lintable_none_when_subprocess_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A git that fails to exec (FileNotFoundError) degrades to None, not a crash."""
    monkeypatch.setattr("garuff.files.shutil.which", lambda _: "/usr/bin/git")

    def boom(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr("garuff.files.subprocess.run", boom)

    assert git_lintable(tmp_path) is None


@needs_git
def test_git_lintable_none_outside_a_work_tree(tmp_path: Path) -> None:
    """A directory that is not a git repo yields None (CalledProcessError branch)."""
    assert git_lintable(tmp_path) is None
