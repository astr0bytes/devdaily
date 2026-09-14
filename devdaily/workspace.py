"""Find git repositories under the workspace roots."""

import os
from pathlib import Path


def find_repos(roots: list[Path], max_depth: int = 3, exclude: set[str] | None = None) -> list[Path]:
    exclude = exclude or set()
    repos = set()
    for root in roots:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            continue
        base_depth = len(root.parts)
        for dirpath, dirnames, _ in os.walk(root):
            current = Path(dirpath)
            if (current / ".git").exists():
                repos.add(current)
                dirnames.clear()  # don't look for nested repositories
                continue
            if len(current.parts) - base_depth >= max_depth:
                dirnames.clear()
                continue
            dirnames[:] = [d for d in dirnames if d not in exclude and not d.startswith(".")]
    return sorted(repos)
