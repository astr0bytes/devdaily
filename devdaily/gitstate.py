"""Collect the state of a repository: recent activity, pending changes, branches."""

import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEP = "\x1f"


class GitError(Exception):
    pass


@dataclass
class RepoState:
    path: Path
    branch: str
    commits: list[str] = field(default_factory=list)
    modified: int = 0
    untracked: int = 0
    ahead: int = 0
    behind: int = 0
    has_upstream: bool = True
    stashes: int = 0
    stale_branches: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def needs_attention(self) -> bool:
        return bool(self.modified or self.untracked or self.ahead or self.behind
                    or self.stashes or self.stale_branches or not self.has_upstream)


def git(repo: Path, *args: str, check: bool = True) -> str:
    try:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=30)
    except FileNotFoundError:
        raise GitError("git is not installed") from None
    except subprocess.TimeoutExpired:
        raise GitError("timed out") from None
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {args[0]} failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def git_user_email() -> str | None:
    try:
        return subprocess.run(["git", "config", "--global", "user.email"],
                              capture_output=True, text=True).stdout.strip() or None
    except FileNotFoundError:
        return None


def _parse_status(repo: Path, state: RepoState) -> None:
    out = git(repo, "status", "--porcelain=v2", "--branch")
    state.has_upstream = False
    for line in out.splitlines():
        if line.startswith("# branch.head "):
            state.branch = line.split(" ", 2)[2]
        elif line.startswith("# branch.upstream "):
            state.has_upstream = True
        elif line.startswith("# branch.ab "):
            ahead, behind = line.split()[2:4]
            state.ahead, state.behind = int(ahead), abs(int(behind))
        elif line.startswith("?"):
            state.untracked += 1
        elif line[:1] in ("1", "2", "u"):
            state.modified += 1
    if state.branch == "(detached)":
        state.has_upstream = True  # detached HEAD, no upstream expected


def _my_commits(repo: Path, since: date, author: str | None) -> list[str]:
    args = ["log", "--branches", "--remotes", "--no-merges", f"--since={since.isoformat()} 00:00",
            "--format=%s"]
    if author:
        args.append(f"--author={author}")
    out = git(repo, *args, check=False)
    return [line for line in out.splitlines() if line]


def _stale_branches(repo: Path, stale_days: int) -> list[str]:
    out = git(repo, "for-each-ref", "refs/heads", f"--format=%(refname:short){SEP}%(committerdate:iso-strict)")
    limit = datetime.now(timezone.utc) - timedelta(days=stale_days)
    stale = []
    for line in out.splitlines():
        name, iso = line.split(SEP)
        if name in ("main", "master", "develop"):
            continue
        if datetime.fromisoformat(iso) < limit:
            stale.append(name)
    return stale


def collect_state(repo: Path, since: date, author: str | None, stale_days: int = 30) -> RepoState:
    state = RepoState(path=repo, branch="?")
    _parse_status(repo, state)
    state.commits = _my_commits(repo, since, author)
    state.stashes = len(git(repo, "stash", "list", check=False).splitlines())
    state.stale_branches = _stale_branches(repo, stale_days)
    return state
