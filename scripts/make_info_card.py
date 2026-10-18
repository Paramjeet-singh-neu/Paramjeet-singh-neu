#!/usr/bin/env python3
"""Neofetch-style panel. Content is taken from the public GitHub profile."""

import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "info-card.svg"

# param-ascii.svg is 560 x 492 and shown at 370px, so it renders 325px tall.
# This card is shown at 490px, so a 490 x 325 viewBox matches that height.
WIDTH = 490
HEIGHT = 325

BG = "#0d1117"
STROKE = "#30363d"
TITLE = "#7ee787"
KEY = "#79c0ff"
VALUE = "#e6edf3"
MUTED = "#8b949e"
RULE = "#30363d"

# Public profile, pinned repos, and language bytes as of the last local build.
# The daily workflow does not rewrite this card.
ROWS = [
    ("now", "AI/ML Engineer"),
    ("focus", "production LLMs, RAG, agents"),
    ("stack", "Python  ·  TypeScript  ·  Go  ·  Java"),
    ("pinned", "CoachMe  ·  ConNET  ·  FinSight  ·  IMBD"),
    ("also", "Trustabl  ·  cursor-boston  ·  CertForge"),
    ("site", "paramjeetsingh.me"),
    ("repos", "34 public"),
]


def main() -> None:
    animate = os.environ.get("STATIC", "0") != "1"
    left = 28
    key_x = left
    val_x = 108
    line = 28
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" role="img">',
        "<title>param@github</title>",
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="16" '
        f'fill="{BG}" stroke="{STROKE}"/>',
    ]

    def group(begin: float, body: str) -> str:
        if not animate:
            return f"<g>{body}</g>"
        return (
            f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.2f}s" dur="0.28s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 10" to="0 0" begin="{begin:.2f}s" dur="0.28s" fill="freeze"/>'
            f"{body}</g>"
        )

    dots = "".join(
        f'<circle cx="{22 + i * 16}" cy="26" r="5" fill="{color}"/>'
        for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840"))
    )
    header = (
        f"{dots}"
        f'<text x="78" y="31" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="13" fill="{MUTED}">param@github ~</text>'
        f'<text x="{left}" y="68" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="20" font-weight="700" fill="{TITLE}">param@github</text>'
        f'<line x1="{left}" y1="82" x2="{WIDTH - left}" y2="82" stroke="{RULE}" stroke-width="1.5"/>'
    )
    parts.append(group(0.05, header))

    font = 'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
    for i, (key, value) in enumerate(ROWS):
        y = 118 + i * line
        body = (
            f'<text x="{key_x}" y="{y}" {font} font-size="15" fill="{KEY}">'
            f"{html.escape(key)}</text>"
            f'<text x="{val_x}" y="{y}" {font} font-size="15" fill="{VALUE}">'
            f"{html.escape(value)}</text>"
        )
        parts.append(group(0.28 + i * 0.12, body))

    parts.append("</svg>")
    DST.write_text("\n".join(parts) + "\n")
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
