#!/usr/bin/env python3
"""Check that the current git branch is named <type>/<kebab-case-description>.

GitHub (ruleset "branch-name") only checks the <type>/ prefix when a branch
is pushed. This hook also checks the description part and catches a bad name
on the first commit, before anything is pushed.
"""

import re
import subprocess
import sys

# Same types as in Conventional Commits (scripts/check_commit_msg.py)
BRANCH_TYPES = (
    "feat",
    "fix",
    "build",
    "chore",
    "ci",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
)

BRANCH_RE = re.compile(rf"^({'|'.join(BRANCH_TYPES)})/[a-z0-9]+(-[a-z0-9]+)*$")

# Branches that are not created by hand
SKIP_EXACT = frozenset(["master", "main"])
SKIP_PREFIXES = ("dependabot/",)


def current_branch() -> str | None:
    """Return the branch name, or None for detached HEAD (CI, rebase)."""
    result = subprocess.run(
        # Fixed arguments, no user input
        ["git", "symbolic-ref", "--short", "-q", "HEAD"],  # noqa: S607
        capture_output=True,
        # git prints ref names as UTF-8; Windows would decode them as cp1252
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def suggest(name: str) -> str:
    """Best-effort suggestion: Front_Signals -> feat/front-signals."""
    prefix, _, rest = name.partition("/")
    if not rest or prefix not in BRANCH_TYPES:
        prefix, rest = "feat", name
    slug = re.sub(r"[^a-z0-9]+", "-", rest.lower()).strip("-")
    return f"{prefix}/{slug or 'short-description'}"


def main() -> int:
    # A Cyrillic branch name must not crash print() on a cp1251 Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    branch = current_branch()
    if branch is None or branch in SKIP_EXACT or branch.startswith(SKIP_PREFIXES):
        return 0
    if BRANCH_RE.match(branch):
        return 0

    types = ", ".join(BRANCH_TYPES)
    print(
        f"Branch name '{branch}' does not match <type>/<description>.\n"
        f"  type: {types}\n"
        "  description: lowercase latin letters, digits and dashes\n"
        "  examples: feat/timer-beep, fix/84-cors-origins\n"
        "GitHub will refuse to push a branch without a valid type/ prefix.\n"
        "Rename the branch before pushing, e.g.:\n"
        f"  git branch -m {suggest(branch)}"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
