#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row is revealed left-to-right with a CSS clip-path wipe on step timing,
staggered top to bottom, with a block cursor riding the wipe edge. Prints once
and freezes -- no looping.

Monochrome by design: per-character colouring is what makes most ASCII
portraits look like static.

  --preview   print the ASCII grid to the terminal instead of writing SVG
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "bryan-ascii.svg"

# Sparse -> dense.
#
# IMPORTANT -- the mapping direction depends on the background. Printed ASCII is
# dark ink on white paper, so a dense glyph reads DARK and dark pixels map to
# dense. This renders light glyphs on a dark card, so a dense glyph lights up
# more pixels and reads BRIGHT: the mapping must be inverted, and BRIGHT pixels
# map to dense. Get this backwards and you render a photographic negative --
# dark hair comes out as the brightest thing on the card.
#
# The paired half of this inversion lives in prep_photo.tone(): background is
# composited to BLACK so it lands on the leading space and disappears.
#
# Ramp length is a legibility control, not a detail control. Long ramps turn
# small tonal variation into speckle; short ramps posterise into clean masses
# that survive being displayed at 370px.
RAMPS = {
    "long": " .`:-=+*cs#%@",
    "mid": " .:-=+*#%@",
    "short": " .:*#@",
}
RAMP = RAMPS["mid"]

COLS = 100
CHAR_W = 6
LINE_H = 12
FONT_SIZE = 11
PAD = 14

BG = "#0d1117"
BORDER = "#21262d"
INK = "#c9d1d9"
CURSOR = "#39d353"

FONT = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", monospace')

ROW_DUR = 0.34      # seconds for one row to type
ROW_STAGGER = 0.035  # delay between consecutive rows


def to_rows(img: Image.Image, cols: int = COLS, ramp: str = RAMP,
            invert: bool = True) -> list[str]:
    """Downsample to a character grid and map luminance onto the ramp.

    invert=True  -> dark pixels become dense glyphs (printed-ASCII convention).
    invert=False -> bright pixels become dense glyphs.
    """
    img = img.convert("L")
    w, h = img.size
    rows = max(1, round(cols * (h / w) * (CHAR_W / LINE_H)))
    img = img.resize((cols, rows), Image.LANCZOS)

    px = list(img.getdata())
    last = len(ramp) - 1
    out: list[str] = []
    for r in range(rows):
        line = []
        for c in range(cols):
            v = px[r * cols + c] / 255.0
            if invert:
                v = 1.0 - v
            line.append(ramp[min(last, int(v * last + 0.5))])
        out.append("".join(line))
    return out


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(rows: list[str], light: bool = False) -> str:
    bg, border, ink, cursor = (
        ("#f6f8fa", "#d0d7de", "#24292f", "#1a7f37") if light
        else (BG, BORDER, INK, CURSOR)
    )
    cols = len(rows[0])
    grid_w = cols * CHAR_W
    grid_h = len(rows) * LINE_H
    width = grid_w + PAD * 2
    height = grid_h + PAD * 2
    steps = max(2, cols // 4)

    parts: list[str] = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="ASCII portrait of Bryan Cruz">')

    add(f"""<style>
    .bg   {{ fill: {bg}; stroke: {border}; }}
    text  {{ font-family: {FONT}; font-size: {FONT_SIZE}px;
             fill: {ink}; white-space: pre; }}
    .r    {{ clip-path: inset(0 100% 0 0);
             animation: type {ROW_DUR}s steps({steps}, end) forwards; }}
    .cur  {{ fill: {cursor}; opacity: 0;
             animation: ride {ROW_DUR}s steps({steps}, end) forwards,
                        gone .01s linear forwards; }}
    @keyframes type {{ to {{ clip-path: inset(0 0 0 0); }} }}
    @keyframes ride {{
      from {{ opacity: 1; transform: translateX(0); }}
      to   {{ opacity: 1; transform: translateX({grid_w - CHAR_W}px); }}
    }}
    @keyframes gone {{ to {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .r   {{ animation: none; clip-path: none; }}
      .cur {{ animation: none; opacity: 0; }}
    }}
  </style>""")

    add(f'<rect class="bg" x=".5" y=".5" width="{width - 1}" '
        f'height="{height - 1}" rx="10"/>')

    for i, line in enumerate(rows):
        delay = round(i * ROW_STAGGER, 3)
        y = PAD + (i + 1) * LINE_H - 3
        add(f'<text class="r" x="{PAD}" y="{y}" xml:space="preserve" '
            f'style="animation-delay:{delay}s">{esc(line)}</text>')
        # Block cursor riding this row's wipe edge, then extinguished.
        add(f'<rect class="cur" x="{PAD}" y="{y - FONT_SIZE + 2}" '
            f'width="{CHAR_W}" height="{FONT_SIZE}" '
            f'style="animation-delay:{delay}s,{round(delay + ROW_DUR, 3)}s"/>')

    add("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="print ASCII to the terminal, write nothing")
    ap.add_argument("--cols", type=int, default=COLS)
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--ramp", choices=sorted(RAMPS), default="mid")
    ap.add_argument("--no-invert", dest="invert", action="store_false",
                    help="map BRIGHT pixels to dense glyphs (pairs with "
                         "prep_photo --bg black)")
    ap.add_argument("--light", action="store_true",
                    help="dark glyphs on a light card")
    args = ap.parse_args()

    if not args.src.exists():
        raise SystemExit(f"missing {args.src} -- run prep_photo.py first")

    rows = to_rows(Image.open(args.src), args.cols, RAMPS[args.ramp],
                   invert=args.invert)

    if args.preview:
        for line in rows:
            print(line.rstrip())
        return

    args.out.write_text(build(rows, light=args.light), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size:,} bytes, "
          f"{args.cols}x{len(rows)} grid, ramp={args.ramp}, "
          f"{'light' if args.light else 'dark'} card)")


if __name__ == "__main__":
    main()
