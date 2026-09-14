"""Output formats: terminal text, stand-up markdown and JSON."""

import json
import sys
from datetime import date

from devdaily.gitstate import RepoState

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def _warnings(s: RepoState) -> list[str]:
    items = []
    if s.modified:
        items.append(f"{s.modified} modified file(s) not committed")
    if s.untracked:
        items.append(f"{s.untracked} untracked file(s)")
    if s.ahead:
        items.append(f"{s.ahead} commit(s) not pushed")
    if s.behind:
        items.append(f"{s.behind} commit(s) behind upstream")
    if not s.has_upstream:
        items.append("branch has no upstream")
    if s.stashes:
        items.append(f"{s.stashes} stash(es)")
    if s.stale_branches:
        items.append(f"stale branches: {', '.join(s.stale_branches[:5])}"
                     + (" ..." if len(s.stale_branches) > 5 else ""))
    return items


def _header(since: date) -> str:
    return f"since {DAYS[since.weekday()]} {since.isoformat()}"


def render_text(states: list[RepoState], since: date, author: str | None, total: int) -> str:
    out = [_c(f"devdaily {date.today().isoformat()} ({_header(since)})", "1"),
           f"{total} repositories scanned, author: {author or 'any'}", ""]
    if not states:
        out.append(_c("Nothing to report, everything is clean.", "32"))
    for s in states:
        out.append(_c(f"* {s.name}", "1;34") + f"  [{s.branch}]  {s.path}")
        for msg in s.commits:
            out.append(_c("    + ", "32") + msg)
        for warn in _warnings(s):
            out.append(_c("    ! ", "33") + warn)
        out.append("")
    nb_commits = sum(len(s.commits) for s in states)
    nb_attention = sum(1 for s in states if s.needs_attention)
    out.append(f"Total: {nb_commits} commit(s), {nb_attention} repository(ies) to check")
    return "\n".join(out)


def render_standup(states: list[RepoState], since: date, author: str | None, total: int) -> str:
    """Markdown summary to paste in Slack or Teams."""
    out = [f"**Stand-up {date.today().isoformat()}** ({_header(since)})", "", "*Done:*"]
    done = [(s.name, msg) for s in states for msg in s.commits]
    out += [f"- `{name}`: {msg}" for name, msg in done] or ["- (no commits)"]
    in_progress = [s for s in states if s.modified or s.ahead]
    out += ["", "*In progress:*"]
    out += [f"- `{s.name}` on `{s.branch}`" for s in in_progress] or ["- (nothing)"]
    return "\n".join(out)


def render_json(states: list[RepoState], since: date, author: str | None, total: int) -> str:
    return json.dumps({
        "date": date.today().isoformat(),
        "since": since.isoformat(),
        "author": author,
        "repos_scanned": total,
        "repos": [{
            "name": s.name, "path": str(s.path), "branch": s.branch, "commits": s.commits,
            "modified": s.modified, "untracked": s.untracked, "ahead": s.ahead, "behind": s.behind,
            "has_upstream": s.has_upstream, "stashes": s.stashes, "stale_branches": s.stale_branches,
        } for s in states],
    }, indent=2, ensure_ascii=False)


RENDERERS = {"text": render_text, "standup": render_standup, "json": render_json}
