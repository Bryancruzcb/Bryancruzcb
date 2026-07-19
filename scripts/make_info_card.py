#!/usr/bin/env python3
"""Hand-author the neofetch-style info card SVG.

Deliberately carries no GitHub stats -- the heatmap already covers those.
This panel is for what the numbers cannot say.

STATIC=1 emits a frozen frame (no animation) for quick local preview.
"""
from __future__ import annotations

import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

WIDTH = 490
PAD = 22
KEY_X = 22
VAL_X = 104
LINE = 19
GROUP_GAP = 5
FONT_SIZE = 12

BG = "#0d1117"
BORDER = "#21262d"
TITLE = "#58a6ff"
KEY = "#7ee787"
VAL = "#c9d1d9"
DIM = "#8b949e"
RULE = "#30363d"

FONT = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", monospace')

TITLE_TEXT = "bryan@github"

# (key, [value lines]) -- wrapped by hand so the monospace column never overflows.
ROWS: list[tuple[str, list[str]]] = [
    ("Now", ["CS @ San Jose State University"]),
    ("Seeking", ["New-grad / junior SWE",
                 "Java backend · full-stack · dev tooling"]),
    ("Stack", ["Java 21 · Spring Boot · JavaFX",
               "React 19 · TypeScript · Python"]),
    ("Ships", ["CreatorFlow · second-brain-tools",
               "signal-path"]),
    ("Habits", ["tests · CI on every push",
                "honest error handling"]),
    ("Where", ["Bay Area, CA — onsite or remote"]),
]

# Classic neofetch terminal-colour blocks.
SWATCHES = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353",
            "#58a6ff", "#a371f7", "#c9d1d9"]

STATIC = os.environ.get("STATIC") == "1"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    total_lines = sum(len(lines) for _, lines in ROWS)
    body_h = total_lines * LINE + (len(ROWS) - 1) * GROUP_GAP
    head_h = PAD + 18 + 16
    height = head_h + body_h + 16 + 20 + PAD

    parts: list[str] = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-label="Profile info card">')

    anim = "" if STATIC else (
        ".row { opacity: 0; animation: slide .5s ease-out forwards; }\n"
        "    @keyframes slide {\n"
        "      from { opacity: 0; transform: translateX(-8px); }\n"
        "      to   { opacity: 1; transform: translateX(0);    }\n"
        "    }\n"
        "    @media (prefers-reduced-motion: reduce) {\n"
        "      .row { animation: none; opacity: 1; transform: none; }\n"
        "    }"
    )

    add(f"""<style>
    .bg  {{ fill: {BG}; stroke: {BORDER}; }}
    text {{ font-family: {FONT}; font-size: {FONT_SIZE}px; }}
    .t   {{ fill: {TITLE}; font-weight: 700; }}
    .k   {{ fill: {KEY}; font-weight: 600; }}
    .v   {{ fill: {VAL}; }}
    .d   {{ fill: {DIM}; }}
    {anim}
  </style>""")

    add(f'<rect class="bg" x=".5" y=".5" width="{WIDTH - 1}" '
        f'height="{height - 1}" rx="10"/>')

    def row(delay: float, body: str) -> None:
        style = "" if STATIC else f' style="animation-delay:{round(delay, 3)}s"'
        cls = "row" if not STATIC else ""
        add(f'<g class="{cls}"{style}>{body}</g>')

    # Title line + rule, mimicking neofetch's user@host header.
    y = PAD + 14
    row(0.0,
        f'<text class="t" x="{KEY_X}" y="{y}">{esc(TITLE_TEXT)}</text>'
        f'<text class="d" x="{KEY_X + 96}" y="{y}">~ neofetch</text>')

    y += 12
    row(0.06, f'<line x1="{KEY_X}" y1="{y}" x2="{WIDTH - PAD}" y2="{y}" '
              f'stroke="{RULE}" stroke-width="1"/>')

    y += 22
    delay = 0.12
    for key, lines in ROWS:
        for i, line in enumerate(lines):
            key_part = (f'<text class="k" x="{KEY_X}" y="{y}">{esc(key)}</text>'
                        if i == 0 else "")
            row(delay,
                key_part +
                f'<text class="v" x="{VAL_X}" y="{y}">{esc(line)}</text>')
            y += LINE
            delay += 0.07
        y += GROUP_GAP

    # Colour blocks.
    y += 2
    blocks = "".join(
        f'<rect x="{KEY_X + i * 20}" y="{y}" width="16" height="10" rx="2" '
        f'fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    row(delay + 0.05, blocks)

    add("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes"
          f"{', STATIC' if STATIC else ''})")


if __name__ == "__main__":
    main()
