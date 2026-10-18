#!/usr/bin/env python3
"""Render the prepped portrait as a one-color ASCII SVG that types itself in."""

import html
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source-prepped.png"
DST = ROOT / "param-ascii.svg"
PREVIEW = ROOT / "preview-ascii.png"

# Bright (sparse) -> dark (dense). The leading space clears the background.
RAMP = " .`:-=+*cs#%@"
COLS = 96
ROWS = 46
FONT = 9
CHAR_W = 5.5
LINE_H = 10
PAD = 16
FILL = "#c9d1d9"
BG = "#0d1117"
CURSOR = "#8b949e"

WIDTH = PAD * 2 + COLS * CHAR_W
HEIGHT = PAD * 2 + ROWS * LINE_H


def fit_grid(image_w: int, image_h: int) -> None:
    """Pick a row count that keeps the photo's proportions in monospace cells."""
    global ROWS, WIDTH, HEIGHT
    ROWS = max(28, round(COLS * image_h / image_w * CHAR_W / LINE_H))
    WIDTH = PAD * 2 + COLS * CHAR_W
    HEIGHT = PAD * 2 + ROWS * LINE_H


def glyphs_from_image(path: Path) -> list[str]:
    im = Image.open(path).convert("L")
    width, height = im.size
    # Drop the lower shirt. Fabric texture turns into noise at this resolution,
    # and the face needs the rows.
    im = im.crop((0, 0, width, int(height * 0.78)))
    fit_grid(*im.size)
    pix = np.asarray(im)
    pix = cv2.bilateralFilter(pix, d=9, sigmaColor=28, sigmaSpace=28)
    # Downsample in two steps so eyes and the smile survive as shapes,
    # not as single noisy pixels.
    mid_w, mid_h = COLS * 2, ROWS * 2
    mid = cv2.resize(pix, (mid_w, mid_h), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(mid, (0, 0), 0.8)
    sharp = cv2.addWeighted(mid, 1.35, blur, -0.35, 0)
    pix = cv2.resize(sharp, (COLS, ROWS), interpolation=cv2.INTER_AREA)
    pix = np.clip(pix, 0, 255).astype(np.int32)
    # Evenly spaced stops on the guide ramp, dark to bright. Neighboring
    # glyphs look alike, and using every one turns a face into static.
    stops = [len(RAMP) - 1, 10, 8, 6, 4, 3, 1, 0]
    edges = [0, 36, 68, 100, 132, 164, 198, 228, 256]
    idx = np.zeros_like(pix)
    for stop, lo, hi in zip(stops, edges[:-1], edges[1:]):
        idx[(pix >= lo) & (pix < hi)] = stop
    idx[pix >= 242] = 0
    return ["".join(RAMP[int(i)] for i in row) for row in idx]


def build_svg(rows: list[str], animate: bool) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.1f} {HEIGHT:.1f}" '
        f'width="{WIDTH:.1f}" height="{HEIGHT:.1f}" role="img">',
        "<title>Param ASCII portrait</title>",
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>',
        "<defs>",
    ]
    row_dur = 0.20
    stagger = 0.052
    for r in range(len(rows)):
        y = PAD + r * LINE_H
        begin = 0.15 + r * stagger
        if animate:
            parts.append(
                f'<clipPath id="row{r}">'
                f'<rect x="0" y="{y:.1f}" height="{LINE_H}" width="0">'
                f'<animate attributeName="width" from="0" to="{WIDTH:.1f}" '
                f'begin="{begin:.3f}s" dur="{row_dur:.2f}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
        else:
            parts.append(
                f'<clipPath id="row{r}"><rect x="0" y="{y:.1f}" '
                f'width="{WIDTH:.1f}" height="{LINE_H}"/></clipPath>'
            )
    parts.append("</defs>")
    for r, line in enumerate(rows):
        y_base = PAD + r * LINE_H + FONT * 0.82
        begin = 0.15 + r * stagger
        parts.append(f'<g clip-path="url(#row{r})">')
        for c, ch in enumerate(line):
            if ch == " ":
                continue
            x = PAD + c * CHAR_W
            parts.append(
                f'<text x="{x:.2f}" y="{y_base:.2f}" '
                f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
                f'font-size="{FONT}" fill="{FILL}">{html.escape(ch)}</text>'
            )
        if animate:
            parts.append(
                f'<rect y="{PAD + r * LINE_H + 1}" width="6" height="{LINE_H - 2}" '
                f'fill="{CURSOR}">'
                f'<animate attributeName="x" from="{PAD}" to="{WIDTH - PAD}" '
                f'begin="{begin:.3f}s" dur="{row_dur:.2f}s" fill="freeze"/>'
                f'<animate attributeName="opacity" from="1" to="0" '
                f'begin="{begin + row_dur:.3f}s" dur="0.06s" fill="freeze"/>'
                f"</rect>"
            )
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_preview(rows: list[str]) -> None:
    font_path = "/System/Library/Fonts/Menlo.ttc"
    size = 15
    try:
        font = ImageFont.truetype(font_path, size)
    except OSError:
        font = ImageFont.load_default()
    char_w, line_h = 9, 16
    pad = 16
    cols = max(len(line) for line in rows)
    canvas = Image.new("RGB", (pad * 2 + cols * char_w, pad * 2 + len(rows) * line_h), BG)
    draw = ImageDraw.Draw(canvas)
    for r, line in enumerate(rows):
        draw.text((pad, pad + r * line_h), line, font=font, fill=FILL)
    canvas.save(PREVIEW)
    print(f"wrote {PREVIEW}")


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}; run scripts/prep_photo.py first")
    rows = glyphs_from_image(SRC)
    animate = os.environ.get("STATIC", "0") != "1"
    DST.write_text(build_svg(rows, animate=animate))
    print(f"wrote {DST} rows={len(rows)} cols={COLS}")
    write_preview(rows)


if __name__ == "__main__":
    main()
