"""Compute the period covered by the report."""

import re
from datetime import date, timedelta


def last_workday(today: date) -> date:
    """On Mondays, go back to Friday; otherwise use the previous day."""
    delta = 3 if today.weekday() == 0 else 2 if today.weekday() == 6 else 1
    return today - timedelta(days=delta)


def parse_since(value: str, today: date | None = None) -> date:
    today = today or date.today()
    value = value.strip().lower()
    if value == "today":
        return today
    if value == "yesterday":
        return today - timedelta(days=1)
    if m := re.fullmatch(r"(\d+)\s*([dw])", value):
        days = int(m.group(1)) * (7 if m.group(2) == "w" else 1)
        return today - timedelta(days=days)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"invalid date: {value!r} (expected YYYY-MM-DD, yesterday, 3d, 1w)") from None
