#!/usr/bin/env python3
"""devdaily - daily summary of your git repositories, handy for stand-ups."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from devdaily import __version__
from devdaily.config import CONFIG_PATH, load_config, write_default_config
from devdaily.gitstate import GitError, collect_state, git_user_email
from devdaily.period import last_workday, parse_since
from devdaily.report import RENDERERS
from devdaily.workspace import find_repos


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devdaily", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-r", "--root", action="append", type=Path,
                        help="directory to scan (repeatable, default: from config)")
    parser.add_argument("--since", help="start date: YYYY-MM-DD, 'yesterday', '3d' (default: last workday)")
    parser.add_argument("--author", help="author email (default: git config user.email)")
    parser.add_argument("-f", "--format", choices=sorted(RENDERERS), default="text")
    parser.add_argument("-a", "--all", action="store_true", help="also show repositories with no activity")
    parser.add_argument("-v", "--verbose", action="store_true", help="list modified and untracked files")
    parser.add_argument("-j", "--jobs", type=int, default=8, help="number of repositories scanned in parallel")
    parser.add_argument("--init-config", action="store_true", help=f"create {CONFIG_PATH}")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.init_config:
        path = write_default_config()
        print(f"Config written to {path}")
        return 0

    config = load_config()
    roots = args.root or config.roots
    since = parse_since(args.since) if args.since else last_workday(date.today())
    author = args.author or config.author or git_user_email()

    repos = find_repos(roots, max_depth=config.max_depth, exclude=config.exclude)
    if not repos:
        print(f"No git repository found in: {', '.join(map(str, roots))}", file=sys.stderr)
        return 1

    def scan(repo):
        try:
            return collect_state(repo, since, author, stale_days=config.stale_days)
        except GitError as exc:
            print(f"warning: {repo}: {exc}", file=sys.stderr)
            return None

    # map() keeps the input order, so the report stays sorted by path
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        states = [s for s in pool.map(scan, repos) if s is not None]

    if not args.all:
        states = [s for s in states if s.needs_attention or s.commits]

    print(RENDERERS[args.format](states, since=since, author=author, total=len(repos), verbose=args.verbose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
