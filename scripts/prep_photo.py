#!/usr/bin/env python3
"""Prepare a photo for ASCII conversion: source-photo -> source-prepped.png.

A flatly-lit face converts to a dark, unreadable blob. Four steps fix that:

  1. Normalise orientation ONCE, up front, then strip EXIF. The supplied photo
     carries EXIF orientation 5, which includes a mirror as well as a rotation;
     PIL and OpenCV disagree about applying it automatically, so normalising
     here prevents a double-applied or mirrored face downstream.
  2. Remove the background with rembg, so the subject is isolated and the
     background maps to the blank end of the ramp.
  3. Boost LOCAL contrast with CLAHE. Global autocontrast is not enough -- local
     adaptation is what separates facial features from dark hair.
  4. Composite onto pure black, then apply tone. Black -- not white -- because
     the ASCII renders as light glyphs on a dark card; see make_ascii_svg.RAMPS.

Because the card is dark, gamma below 1 does double duty: it lifts very dark
hair out of pure black so the silhouette survives, instead of dissolving into
the background.

Tone settings are photo-specific and load-bearing. Use --preview to iterate:

    python scripts/prep_photo.py photo.jpg --preview --gamma 0.5 --contrast 1.8
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"

WORK_MAX = 1600  # downscale before rembg; plenty for a 100-column grid


def load_oriented(path: Path) -> Image.Image:
    """Load, apply EXIF orientation, then discard the tag entirely."""
    img = Image.open(path)
    orientation = img.getexif().get(274, 1)
    img = ImageOps.exif_transpose(img).convert("RGB")
    clean = Image.new("RGB", img.size)
    clean.putdata(list(img.getdata()))
    print(f"  orientation {orientation} normalised -> {clean.size}")
    return clean


def cut_background(img: Image.Image) -> Image.Image:
    from rembg import remove

    if max(img.size) > WORK_MAX:
        img = img.copy()
        img.thumbnail((WORK_MAX, WORK_MAX), Image.LANCZOS)
    cut = remove(img)
    return cut.convert("RGBA")


def crop_fractions(img: Image.Image, spec: str) -> Image.Image:
    left, top, right, bottom = (float(v) for v in spec.split(","))
    w, h = img.size
    return img.crop((int(left * w), int(top * h), int(right * w), int(bottom * h)))


def tone(rgba: Image.Image, clip: float, grid: int,
         gamma: float, contrast: float, bg: str) -> Image.Image:
    """CLAHE on the subject, composite onto bg, then gamma and contrast."""
    arr = np.array(rgba)
    gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
    alpha = arr[:, :, 3]

    if clip > 0:
        gray = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid)).apply(gray)

    # The background must land on the ramp's blank end, which depends on the
    # mapping direction downstream: --bg white pairs with make_ascii_svg
    # --invert (dark->dense), --bg black pairs with the default (bright->dense).
    out = np.where(alpha > 12, gray, 255 if bg == "white" else 0).astype(np.float32)

    out = 255.0 * np.power(out / 255.0, gamma)
    out = (out - 128.0) * contrast + 128.0
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="L")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", type=Path)
    # Defaults determined empirically by sweep, not copied from the article --
    # its values render this photo as an unreadable blob. CLAHE above ~1.5
    # amplifies local texture and destroys the large tonal masses a portrait
    # needs to read at small size.
    ap.add_argument("--gamma", type=float, default=0.75,
                    help="<1 brightens midtones (default 0.75)")
    ap.add_argument("--contrast", type=float, default=2.0)
    ap.add_argument("--crop", default="0.12,0.02,0.90,0.72",
                    help="left,top,right,bottom as fractions")
    ap.add_argument("--clahe-clip", type=float, default=1.2,
                    help="0 disables CLAHE entirely")
    ap.add_argument("--clahe-grid", type=int, default=8)
    ap.add_argument("--preview", action="store_true",
                    help="print ASCII to the terminal, write nothing")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--ramp", default="mid", help="preview ramp: long|mid|short")
    ap.add_argument("--bg", choices=("black", "white"), default="white",
                    help="what the removed background becomes; must match the "
                         "mapping direction in make_ascii_svg")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    print(f"prep {args.photo.name}  gamma={args.gamma} contrast={args.contrast} "
          f"crop={args.crop} clahe={args.clahe_clip}/{args.clahe_grid}")

    img = load_oriented(args.photo)
    cut = cut_background(img)
    cut = crop_fractions(cut, args.crop)
    prepped = tone(cut, args.clahe_clip, args.clahe_grid,
                   args.gamma, args.contrast, args.bg)

    if args.preview:
        from make_ascii_svg import RAMPS, to_rows
        for line in to_rows(prepped, args.cols, RAMPS[args.ramp],
                            invert=args.bg == "white"):
            print(line.rstrip())
        return

    prepped.save(args.out)
    print(f"wrote {args.out} ({prepped.size[0]}x{prepped.size[1]})")


if __name__ == "__main__":
    main()
