"""User configuration (~/.config/devdaily/config.toml)."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "devdaily" / "config.toml"

DEFAULT_CONFIG = """\
# Directories containing your git repositories
roots = ["~/dev", "~/projects"]

# How deep to look for repositories
max_depth = 3

# Directory names skipped during the scan
exclude = ["node_modules", ".venv", "venv", "vendor", "target", "build", "dist"]

# Local branches without a commit for this many days are reported
stale_days = 30

# Author email (default: git config user.email)
# author = "me@example.com"
"""


@dataclass
class Config:
    roots: list[Path] = field(default_factory=lambda: [Path.cwd()])
    max_depth: int = 3
    exclude: set[str] = field(default_factory=lambda: {"node_modules", ".venv", "venv"})
    stale_days: int = 30
    author: str | None = None


def load_config(path: Path = CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text())
    config = Config()
    if "roots" in data:
        config.roots = [Path(r).expanduser() for r in data["roots"]]
    config.max_depth = data.get("max_depth", config.max_depth)
    config.exclude = set(data.get("exclude", config.exclude))
    config.stale_days = data.get("stale_days", config.stale_days)
    config.author = data.get("author")
    return config


def write_default_config(path: Path = CONFIG_PATH) -> Path:
    if path.exists():
        raise SystemExit(f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG)
    return path
