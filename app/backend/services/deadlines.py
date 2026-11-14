"""Deadline math + commitment parsing (P0-8). Pure functions are unit-tested.

Default windows are FixIt defaults, NOT legal deadlines.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from .. import config

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
     "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
SEV_ORDER = {"routine": 0, "urgent": 1, "emergency": 2}


def worst_severity(sevs: list[str]) -> str:
    return max(sevs or ["routine"], key=lambda s: SEV_ORDER.get(s, 0))


def default_due(severity: str, now: datetime) -> datetime:
    return now + timedelta(hours=config.DEFAULT_WINDOW_HOURS.get(severity, 7 * 24))


def end_of_day(d: datetime) -> datetime:
    return d.replace(hour=17, minute=0, second=0, microsecond=0)


def parse_commitment(text: str, now: datetime) -> datetime | None:
    """Extract a promised repair date from free text. Returns 5pm on that day, or None if vague/refused."""
    t = (text or "").lower()
    if re.search(r"\b(no|not|won't|can't|cannot|refuse)\b.*\b(fix|repair|come|send)\b", t) and not re.search(
            r"\b(by|on|until)\b", t):
        return None
    if "today" in t or "tonight" in t:
        return end_of_day(now)
    if "day after tomorrow" in t:
        return end_of_day(now + timedelta(days=2))
    if "tomorrow" in t:
        return end_of_day(now + timedelta(days=1))
    m = re.search(r"\bin (\d+|a|one|two|three|four|five|six|seven|ten|fourteen) (day|days|week|weeks)\b", t)
    if m:
        words = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "ten": 10,
                 "fourteen": 14}
        n = int(m.group(1)) if m.group(1).isdigit() else words[m.group(1)]
        days = n * (7 if m.group(2).startswith("week") else 1)
        return end_of_day(now + timedelta(days=days))
    # Explicit weekdays/dates win over vague week phrases: "we're busy this week ... Thursday" means Thursday.
    for i, wd in enumerate(WEEKDAYS):
        if re.search(rf"\b{wd}\b", t):
            ahead = (i - now.weekday()) % 7 or 7
            if re.search(rf"\bnext {wd}\b", t) and ahead < 3:
                ahead += 7
            return end_of_day(now + timedelta(days=ahead))
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", t)
    if m:
        mo, d = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else now.year
        y = y + 2000 if y < 100 else y
        try:
            cand = datetime(y, mo, d, 17)
            if not m.group(3) and cand < now - timedelta(days=1):
                cand = cand.replace(year=y + 1)
            return cand
        except ValueError:
            return None
    m = re.search(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.? (\d{1,2})(?:st|nd|rd|th)?\b", t)
    if m:
        try:
            cand = datetime(now.year, MONTHS[m.group(1)], int(m.group(2)), 17)
            if cand < now - timedelta(days=1):
                cand = cand.replace(year=now.year + 1)
            return cand
        except ValueError:
            return None
    if re.search(r"\b(end of (the )?week|this week)\b", t):
        return end_of_day(now + timedelta(days=(4 - now.weekday()) % 7))  # this Friday (today if Friday)
    if "next week" in t:
        return end_of_day(now + timedelta(days=7 - now.weekday()))  # next Monday
    return None


def status_at(due: datetime, now: datetime, current: str = "open") -> str:
    if current in ("met", "escalated"):
        return current
    return "missed" if now > due else "open"


def time_left(due: datetime, now: datetime) -> dict:
    secs = int((due - now).total_seconds())
    neg = secs < 0
    secs = abs(secs)
    return {"overdue": neg, "days": secs // 86400, "hours": (secs % 86400) // 3600, "minutes": (secs % 3600) // 60,
            "total_seconds": -secs if neg else secs}
