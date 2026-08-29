"""Shared helpers: which files in the tree are actually part of the template.

`documents/`, `applications/` and the local build notes are gitignored - they
belong to whoever is using the workspace, not to the repository. Tests that
assert on "what ships" must not read them.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _literal_ignore_names():
    """Literal (non-glob) entries in .gitignore, as a set of names."""
    names = set()
    for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!")) and not any(
            char in line for char in "*?["
        ):
            names.add(line.rstrip("/"))
    return names


_LITERAL_IGNORES = _literal_ignore_names()
_IGNORED_DIRS = {"documents", "applications", "job_scraper", ".git", "__pycache__"}


def is_ignored(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT)
    # Only the top-level directory counts. Matching any part meant a nested
    # folder that merely shared a name - templates/documents/, say - was
    # treated as the user's own and silently skipped by every privacy scan
    # that reads shipped_files().
    if relative.parts[0] in _IGNORED_DIRS:
        # documents/README.md and the .gitkeep markers are tracked: they are
        # the folder contract the template ships. Everything else there is the
        # user's own.
        return relative.name not in ("README.md", ".gitkeep")
    if str(relative) in _LITERAL_IGNORES or relative.name in _LITERAL_IGNORES:
        return True
    return False


def shipped_files(*patterns) -> list:
    """Every file matching the patterns that is part of the template."""
    seen = {}
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file() and not is_ignored(path):
                seen[path] = None
    return sorted(seen)


def git_ignores(path: Path) -> bool:
    """Ask git itself, when this working copy is a repository."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(path)],
        capture_output=True,
    )
    if result.returncode == 128:  # not a git repository (yet)
        return is_ignored(path)
    return result.returncode == 0
