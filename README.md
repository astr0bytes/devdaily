# devdaily

Morning summary of the git repositories in your workspace. For each repository it shows
what you committed since the last workday, and what is still pending: uncommitted
changes, unpushed commits, forgotten stashes, stale branches.

I mostly use it before the daily stand-up, with `-f standup` to get something I can paste
in the team channel.

## Install

Python 3.11 or later, no dependencies.

```
git clone <repo-url> ~/tools/devdaily
```

## Usage

```
python main.py --init-config        # writes ~/.config/devdaily/config.toml
python main.py                      # repositories listed in the config
python main.py -r ~/dev -r ~/work   # explicit roots
python main.py --since 1w -a        # last week, include quiet repositories
python main.py -v                   # also list modified and untracked files
python main.py --fetch              # fetch remotes first, slower but accurate
python main.py -f standup
python main.py -f json
```

On Monday the default period starts on Friday. `--since` accepts `YYYY-MM-DD`,
`yesterday`, `today`, `3d` or `2w`.

Ahead/behind counts are computed against the remote-tracking branches as they are
locally. Use `--fetch` to update them before the scan.

## Configuration

```toml
roots = ["~/dev", "~/projects"]
max_depth = 3
exclude = ["node_modules", ".venv", "vendor"]
stale_days = 30
# author = "me@example.com"
```

## Running it every morning

From `~/.bashrc`, once a day:

```
if [ "$(cat ~/.cache/devdaily.last 2>/dev/null)" != "$(date +%F)" ]; then
    python3 ~/tools/devdaily/main.py && date +%F > ~/.cache/devdaily.last
fi
```

Or with cron on weekdays:

```
0 9 * * 1-5  python3 ~/tools/devdaily/main.py -f standup > ~/standup.md
```
