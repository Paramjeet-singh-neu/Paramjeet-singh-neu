#!/usr/bin/env python3
"""Draw data/contributions.json as a 53-week calendar that reveals once."""

import html
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "contributions.json"
DST = ROOT / "contrib-heatmap.svg"

# none -> brightest. Level 5 is the neon top end past GitHub's usual 0-4.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
MUTED = "#8b949e"
TEXT = "#e6edf3"
STROKE = "#30363d"

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT = 34
TOP = 28
PAD = 16


def shade(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 6:
        return 2
    if count <= 12:
        return 3
    if count <= 22:
        return 4
    return 5


def weeks_of(days: list[dict]) -> list[list[dict | None]]:
    """Sunday-start columns, matching the profile contribution graph."""
    columns: list[list[dict | None]] = []
    current: list[dict | None] | None = None
    for day in days:
        weekday = (datetime.strptime(day["date"], "%Y-%m-%d").weekday() + 1) % 7
        if current is None or weekday == 0:
            if current is not None and len(current) < 7:
                current.extend([None] * (7 - len(current)))
            current = [None] * weekday
            columns.append(current)
        current.append(day)
    if current is not None and len(current) < 7:
        current.extend([None] * (7 - len(current)))
    return columns


def month_labels(columns: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Label the week that contains the 1st. Drop a name if it would sit on the previous one."""
    raw: list[tuple[int, str]] = []
    seen: set[str] = set()
    for index, column in enumerate(columns):
        for day in column:
            if not day:
                continue
            stamp = datetime.strptime(day["date"], "%Y-%m-%d")
            if stamp.day > 7:
                continue
            key = stamp.strftime("%Y-%m")
            if key in seen:
                continue
            seen.add(key)
            raw.append((index, stamp.strftime("%b")))
            break
    labels: list[tuple[int, str]] = []
    for pos, item in enumerate(raw):
        index, _name = item
        nxt = raw[pos + 1][0] if pos + 1 < len(raw) else None
        if nxt is not None and nxt - index < 2:
            continue
        if labels and index - labels[-1][0] < 2:
            continue
        labels.append(item)
    return labels


def days_label(n: int) -> str:
    return f"{n} day" if n == 1 else f"{n} days"


def main() -> None:
    data = json.loads(SRC.read_text())
    columns = weeks_of(data["days"])
    grid_w = len(columns) * STEP
    grid_h = 7 * STEP
    width = PAD + LEFT + grid_w + PAD
    height = PAD + TOP + grid_h + 78
    best = data["best_day"]
    best_label = datetime.strptime(best["date"], "%Y-%m-%d").strftime("%b %-d")
    total = f"{data['total']:,}"
    footer_a = f"{total} contributions in the last year"
    footer_b = (
        f"streak {days_label(data['current_streak'])}"
        f"   ·   longest {days_label(data['longest_streak'])}"
        f"   ·   best {best['count']} on {best_label}"
    )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">',
        f"<title>{html.escape(data['username'])} contributions</title>",
        "<style>",
        "  .cell {",
        "    transform-box: fill-box;",
        "    transform-origin: center;",
        "    animation: reveal 0.4s ease-out both;",
        "  }",
        "  @keyframes reveal {",
        "    from { opacity: 0; transform: translate(-6px, -6px); }",
        "    to { opacity: 1; transform: none; }",
        "  }",
        "</style>",
        f'<rect width="100%" height="100%" rx="12" fill="{BG}" stroke="{STROKE}"/>',
        '<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    ]
    for index, name in month_labels(columns):
        x = PAD + LEFT + index * STEP
        parts.append(
            f'<text x="{x}" y="{PAD + 16}" fill="{MUTED}" font-size="12">{name}</text>'
        )
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD + TOP + row * STEP + 10
        parts.append(
            f'<text x="{PAD}" y="{y}" fill="{MUTED}" font-size="11">{label}</text>'
        )

    for col, column in enumerate(columns):
        for row, day in enumerate(column):
            if day is None:
                continue
            color = PALETTE[shade(day["count"])]
            x = PAD + LEFT + col * STEP
            y = PAD + TOP + row * STEP
            delay = (col + row) * 0.012
            tip = f"{day['count']} on {day['date']}"
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" style="animation-delay:{delay:.3f}s">'
                f"<title>{html.escape(tip)}</title>"
                f"</rect>"
            )

    legend_y = PAD + TOP + grid_h + 8
    legend = "Less"
    parts.append(
        f'<text x="{PAD + LEFT}" y="{legend_y + 12}" fill="{MUTED}" font-size="12">{legend}</text>'
    )
    lx = PAD + LEFT + 42
    for color in PALETTE:
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
        lx += STEP
    parts.append(
        f'<text x="{lx + 4}" y="{legend_y + 12}" fill="{MUTED}" font-size="12">More</text>'
    )
    parts.append(
        f'<text x="{PAD + LEFT}" y="{legend_y + 40}" fill="{TEXT}" font-size="14">'
        f"{html.escape(footer_a)}</text>"
    )
    parts.append(
        f'<text x="{PAD + LEFT}" y="{legend_y + 60}" fill="{MUTED}" font-size="12">'
        f"{html.escape(footer_b)}</text>"
    )
    parts.append("</g></svg>")
    DST.write_text("\n".join(parts) + "\n")
    print(f"wrote {DST} weeks={len(columns)} {width}x{height}")


if __name__ == "__main__":
    main()
