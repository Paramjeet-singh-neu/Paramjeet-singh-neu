#!/usr/bin/env python3
"""Turn a portrait into a high-contrast grayscale plate for ASCII art.

Background is removed, local contrast is lifted, and the subject is
composited onto white so empty space maps to the blank end of the ramp.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def remove_background(im: Image.Image) -> Image.Image:
    from rembg import remove

    return remove(im).convert("RGBA")


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "source-photo.jpg")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "source-prepped.png")
    cut = remove_background(Image.open(src).convert("RGBA"))
    arr = np.array(cut)
    rgb, alpha = arr[:, :, :3], arr[:, :, 3]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    blur = cv2.GaussianBlur(eq, (0, 0), 1.1)
    sharp = cv2.addWeighted(eq, 1.55, blur, -0.55, 0)

    subject = alpha.astype(np.float32) / 255.0
    out = sharp.astype(np.float32) * subject + 255.0 * (1.0 - subject)
    out = np.clip(out, 0, 255).astype(np.uint8)

    ys, xs = np.where(alpha > 24)
    if len(xs) == 0:
        raise SystemExit("background removal left an empty subject")
    pad = 10
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(out.shape[0], int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(out.shape[1], int(xs.max()) + pad + 1)
    cropped = out[y0:y1, x0:x1]
    Image.fromarray(cropped, mode="L").save(dst)
    print(f"wrote {dst} {cropped.shape[1]}x{cropped.shape[0]}")


if __name__ == "__main__":
    main()
