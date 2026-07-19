#!/usr/bin/env python3
"""Scrape the public GitHub contribution calendar into data/contributions.json.

No token, no GraphQL -- GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions, the same fragment the
profile page itself uses.

Runs daily in CI. Fails loudly rather than committing an empty graph: see
validate() for the guard, and the spec's section 6.3 for why that matters.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Bryancruzcb"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

# A full year is 365-366 cells. Anything well below that means GitHub changed
# the markup and our selectors are silently matching the wrong thing.
MIN_CELLS = 300

TIMEOUT = 30
HEADERS = {
    "User-Agent": f"{USERNAME}-profile-art/1.0 (+https://github.com/{USERNAME})",
    "Accept": "text/html",
}

# "1 contribution on July 12th." / "12 contributions on ..." / "No contributions on ..."
COUNT_RE = re.compile(r"^\s*(No|[\d,]+)\s+contribution", re.IGNORECASE)


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    """Return [{date, level, count}, ...] sorted by date.

    Levels live on the <td>; exact counts do not -- they are only in the
    sibling <tool-tip>, joined by tool-tip[for] == td[id].
    """
    soup = BeautifulSoup(html, "html.parser")

    tips: dict[str, str] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tips[target] = tip.get_text(strip=True)

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day"):
        iso = cell.get("data-date")
        if not iso:
            continue

        count = 0
        tip_text = tips.get(cell.get("id", ""), "")
        match = COUNT_RE.match(tip_text)
        if match:
            token = match.group(1)
            if token.lower() != "no":
                count = int(token.replace(",", ""))

        days.append(
            {
                "date": iso,
                "level": int(cell.get("data-level") or 0),
                "count": count,
            }
        )

    days.sort(key=lambda d: d["date"])
    return days


def validate(days: list[dict]) -> None:
    """Fail the CI run rather than commit a blank heatmap over a good one."""
    if len(days) < MIN_CELLS:
        sys.exit(
            f"FATAL: parsed only {len(days)} day cells (expected >= {MIN_CELLS}).\n"
            f"GitHub likely changed the markup at {URL}.\n"
            f"Refusing to write data -- the previous heatmap stays live."
        )

    if not any(d["level"] > 0 for d in days):
        sys.exit(
            f"FATAL: parsed {len(days)} cells but every level is 0.\n"
            f"That means the selector matched but the attribute did not.\n"
            f"Refusing to write data -- the previous heatmap stays live."
        )


def compute_stats(days: list[dict]) -> dict:
    counts = {d["date"]: d["count"] for d in days}
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"] > 0]

    # Longest streak of consecutive active days.
    longest = run = 0
    prev: date | None = None
    for day in days:
        current = date.fromisoformat(day["date"])
        if day["count"] > 0:
            run = run + 1 if prev and current - prev == timedelta(days=1) else 1
            longest = max(longest, run)
        else:
            run = 0
        prev = current

    # Current streak, walking backwards from the most recent day. A zero on the
    # final day does not break it -- that day is still in progress.
    current_streak = 0
    if days:
        cursor = date.fromisoformat(days[-1]["date"])
        if counts.get(cursor.isoformat(), 0) == 0:
            cursor -= timedelta(days=1)
        while counts.get(cursor.isoformat(), 0) > 0:
            current_streak += 1
            cursor -= timedelta(days=1)

    best = max(days, key=lambda d: d["count"]) if days else {"date": None, "count": 0}

    last30 = days[-30:]
    monthly: dict[str, int] = defaultdict(int)
    for day in days:
        monthly[day["date"][:7]] += day["count"]

    return {
        "total": total,
        "active_days": len(active),
        "window_days": len(days),
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_last_30": sum(1 for d in last30 if d["count"] > 0),
        "total_last_30": sum(d["count"] for d in last30),
        "monthly": dict(sorted(monthly.items())),
    }


def main() -> None:
    days = parse_days(fetch_html())
    validate(days)

    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "source": URL,
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": stats,
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {OUT}")
    print(
        f"  {len(days)} days  {stats['total']} contributions  "
        f"{stats['active_days']} active  streak {stats['current_streak']}"
    )


if __name__ == "__main__":
    main()
