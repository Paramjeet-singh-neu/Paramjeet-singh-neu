#!/usr/bin/env python3
"""Scrape the public contribution calendar. No token and no GraphQL."""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GITHUB_USERNAME", "Paramjeet-singh-neu")
OUT = ROOT / "data" / "contributions.json"
URL = f"https://github.com/users/{USERNAME}/contributions"


def parse_count(text: str) -> int:
    cleaned = " ".join(text.split())
    if cleaned.lower().startswith("no contribution"):
        return 0
    match = re.match(r"(\d+)\s+contribution", cleaned, re.I)
    if not match:
        raise ValueError(f"unrecognized contribution tooltip: {cleaned!r}")
    return int(match.group(1))


def streak_stats(days: list[dict]) -> tuple[int, int]:
    longest = current = 0
    for day in days:
        if day["count"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    # A trailing empty cell is "today" before any commits land. Do not break
    # the streak on that single open day.
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    current = 0
    for day in reversed(tail):
        if day["count"] > 0:
            current += 1
        else:
            break
    return current, longest


def main() -> None:
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-heatmap)"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if len(cells) < 300:
        raise SystemExit(f"expected a year of days, found {len(cells)} at {URL}")

    days = []
    for cell in cells:
        tip = None
        cell_id = cell.get("id")
        if cell_id:
            tip = soup.select_one(f'tool-tip[for="{cell_id}"]')
        count = parse_count(tip.get_text(" ", strip=True)) if tip else 0
        days.append(
            {
                "date": cell["data-date"],
                "count": count,
                "level": int(cell.get("data-level", "0")),
            }
        )
    days.sort(key=lambda day: day["date"])
    current, longest = streak_stats(days)
    best = max(days, key=lambda day: (day["count"], day["date"]))
    monthly: dict[str, int] = defaultdict(int)
    for day in days:
        monthly[day["date"][:7]] += day["count"]

    payload = {
        "username": USERNAME,
        "source": URL,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(day["count"] for day in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "monthly": [{"month": month, "count": monthly[month]} for month in sorted(monthly)],
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"wrote {OUT} total={payload['total']} days={len(days)} "
        f"streak={current} longest={longest} best={best['count']} on {best['date']}"
    )


if __name__ == "__main__":
    main()
