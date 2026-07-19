#!/usr/bin/env python3
"""Render data/contributions.json as an animated contribution heatmap SVG.

Self-contained: all motion is CSS keyframes inside the SVG, because GitHub
strips <script> from READMEs but does play SVG animation embedded via <img>.
Reveals once on load with a diagonal wave, then freezes -- no looping.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# How many trailing weeks to draw. Narrowing this to a denser recent window
# (e.g. 12) is a one-line change -- see the design spec, section 4.2.
WEEKS = 53

WIDTH = 860
CELL = 11
GAP = 3
STEP = CELL + GAP
RADIUS = 2

PAD = 24
LABEL_W = 34          # weekday label gutter
MONTH_H = 22          # month label strip

BG = "#0d1117"
BORDER = "#21262d"
TEXT_DIM = "#8b949e"
TEXT = "#c9d1d9"
ACCENT = "#39d353"

# Indexed by data-level 0..4. GitHub never emits a level 5 -- see spec 6.4.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

FONT = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", monospace')

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def sunday_index(d: date) -> int:
    """GitHub columns start on Sunday; Python's weekday() starts on Monday."""
    return (d.weekday() + 1) % 7


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build() -> str:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload["days"]
    stats = payload["stats"]

    days = days[-(WEEKS * 7):]
    first = date.fromisoformat(days[0]["date"])
    offset = sunday_index(first)
    columns = (len(days) + offset + 6) // 7

    grid_w = columns * STEP - GAP
    content_w = LABEL_W + grid_w
    grid_x = max(PAD, (WIDTH - content_w) // 2) + LABEL_W
    grid_y = PAD + MONTH_H

    height = grid_y + 7 * STEP - GAP + 46 + PAD

    parts: list[str] = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-label="GitHub contribution heatmap">')

    add(f"""<style>
    .bg   {{ fill: {BG}; stroke: {BORDER}; }}
    text  {{ font-family: {FONT}; }}
    .lbl  {{ fill: {TEXT_DIM}; font-size: 10px; }}
    .foot {{ fill: {TEXT_DIM}; font-size: 11px; }}
    .hi   {{ fill: {ACCENT}; font-size: 11px; font-weight: 600; }}
    .day  {{ opacity: 0; animation: reveal .45s ease-out forwards; }}
    .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translateY(-5px) scale(.82); }}
      to   {{ opacity: 1; transform: translateY(0)     scale(1);  }}
    }}
    @keyframes fade {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    @media (prefers-reduced-motion: reduce) {{
      .day, .fade {{ animation: none; opacity: 1; transform: none; }}
    }}
  </style>""")

    add(f'<rect class="bg" x=".5" y=".5" width="{WIDTH - 1}" '
        f'height="{height - 1}" rx="10"/>')

    # Month labels, placed at the column where each month first appears.
    # A partial first month sits only a column or two from the next one, so
    # enforce a minimum gap or the two labels overlap into mojibake ("JuAug").
    seen: set[str] = set()
    last_x = -1e9
    MIN_LABEL_GAP = 26
    for i, day in enumerate(days):
        d = date.fromisoformat(day["date"])
        key = day["date"][:7]
        if key in seen:
            continue
        seen.add(key)
        col = (i + offset) // 7
        if col >= columns - 1:
            continue
        x = grid_x + col * STEP
        if x - last_x < MIN_LABEL_GAP:
            continue
        last_x = x
        delay = round(col * 0.018, 3)
        add(f'<text class="lbl fade" x="{x}" y="{PAD + 12}" '
            f'style="animation-delay:{delay}s">{MONTHS[d.month - 1]}</text>')

    # Weekday gutter -- Mon/Wed/Fri, matching GitHub.
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = grid_y + row * STEP + CELL - 2
        add(f'<text class="lbl fade" x="{grid_x - 8}" y="{y}" '
            f'text-anchor="end" style="animation-delay:.1s">{name}</text>')

    # The grid. Diagonal wave: delay keys off (column + row).
    for i, day in enumerate(days):
        idx = i + offset
        col, row = idx // 7, idx % 7
        x = grid_x + col * STEP
        y = grid_y + row * STEP
        level = max(0, min(4, int(day["level"])))
        delay = round((col + row) * 0.018, 3)
        count = day["count"]
        label = f'{count} contribution{"" if count == 1 else "s"} on {day["date"]}'
        add(f'<rect class="day" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{PALETTE[level]}" '
            f'style="animation-delay:{delay}s;transform-origin:{x + CELL / 2}px {y + CELL / 2}px">'
            f'<title>{esc(label)}</title></rect>')

    # Footer: legend left, stats right. Fades in after the grid finishes.
    foot_y = grid_y + 7 * STEP + 18
    tail = round(columns * 0.018 + 0.5, 3)

    add(f'<g class="fade" style="animation-delay:{tail}s">')
    add(f'<text class="foot" x="{grid_x}" y="{foot_y}">Less</text>')
    lx = grid_x + 34
    for level, color in enumerate(PALETTE):
        add(f'<rect x="{lx + level * (CELL + 3)}" y="{foot_y - 9}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{color}"/>')
    add(f'<text class="foot" x="{lx + 5 * (CELL + 3) + 6}" y="{foot_y}">More</text>')

    right = grid_x + grid_w
    streak = stats["current_streak"]
    best = stats["best_day"]
    add(f'<text class="foot" x="{right}" y="{foot_y}" text-anchor="end">'
        f'<tspan class="hi">{streak}-day streak</tspan>'
        f'<tspan> · {stats["active_last_30"]} active days in the last 30 '
        f'· best day {best["count"]}</tspan></text>')
    add("</g>")

    add("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size:,} bytes, WEEKS={WEEKS})")


if __name__ == "__main__":
    main()
