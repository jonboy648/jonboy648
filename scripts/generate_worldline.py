"""Draw a GitHub contribution calendar as a "worldline": a single glowing
trace through a faint Minkowski-diagram grid, spiking upward on days with
commits, with the busiest days marked as event nodes. Named for Jon's
quantum-worldline (MERA / tensor-network) repo.

    python generate_worldline.py calendar.json out_dir

No third-party deps (stdlib only): json, math, datetime, xml.etree for the
self-check's parse assertion.
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

W, H = 880, 220
LEFT, RIGHT, TOP, BOT = 34, 20, 34, 40
PLOT_W = W - LEFT - RIGHT
PLOT_H = H - TOP - BOT
BASELINE_Y = TOP + PLOT_H
MAX_AMP = PLOT_H - 16
MIN_AMP = 6
TOP_N = 6
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

THEMES = {
    "dark": {"bg": "#0B0E17", "grid": "#1E2638", "axis": "#2A3348", "text": "#9198A1",
              "strong": "#E6EDF3", "trail0": "#6A5ACD", "trail1": "#30D6C8",
              "node": "#FFD36E", "stem": "#3A4660"},
    "light": {"bg": "#F6F7FB", "grid": "#E1E6F0", "axis": "#CBD3E3", "text": "#59636E",
               "strong": "#1F2328", "trail0": "#5A3FD6", "trail1": "#0E9488",
               "node": "#C8860D", "stem": "#AEB8CF"},
}


def flat_days(cal):
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    return days


def amp_for(count, maxcount):
    if count <= 0 or maxcount <= 0:
        return 0.0
    return MIN_AMP + (MAX_AMP - MIN_AMP) * math.sqrt(count) / math.sqrt(maxcount)


def draw(cal, theme):
    t = THEMES[theme]
    days = flat_days(cal)
    n = len(days)
    counts = [d["contributionCount"] for d in days]
    maxcount = max(counts) if counts else 0
    active = sum(1 for c in counts if c > 0)
    step = PLOT_W / (n - 1) if n > 1 else 0
    xs = [LEFT + i * step for i in range(n)]
    ys = [BASELINE_Y - amp_for(c, maxcount) for c in counts]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{cal["totalContributions"]} contributions over {n} days, '
        f'plotted as a worldline">',
        "<style>",
        f"text{{font-family:Consolas,Menlo,monospace;font-size:10px;fill:{t['text']}}}",
        ".trail{stroke-dasharray:2600;stroke-dashoffset:2600;animation:draw 3.2s ease-out forwards}",
        "@keyframes draw{to{stroke-dashoffset:0}}",
        ".node{animation:pulse 2.4s ease-in-out infinite}",
        "@keyframes pulse{0%,100%{opacity:.55}50%{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){.trail{animation:none;stroke-dashoffset:0}"
        ".node{animation:none;opacity:1}}",
        "</style>",
        f'<defs><linearGradient id="g-{theme}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["trail0"]}"/><stop offset="100%" stop-color="{t["trail1"]}"/>'
        "</linearGradient>",
        f'<filter id="f-{theme}" x="-40%" y="-200%" width="180%" height="500%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{t["bg"]}"/>',
    ]

    # faint Minkowski light-cone grid: diagonals + month verticals
    for k in range(-4, int(PLOT_W / 40) + 5):
        gx = LEFT + k * 40
        out.append(f'<line x1="{gx}" y1="{TOP - 10}" x2="{gx + PLOT_H + 10}" y2="{BASELINE_Y + 10}" '
                    f'stroke="{t["grid"]}" stroke-width="1"/>')
        out.append(f'<line x1="{gx}" y1="{BASELINE_Y + 10}" x2="{gx + PLOT_H + 10}" y2="{TOP - 10}" '
                    f'stroke="{t["grid"]}" stroke-width="1"/>')
    out.append(f'<rect x="0" y="0" width="{LEFT - 1}" height="{H}" fill="{t["bg"]}"/>')
    out.append(f'<rect x="{W - RIGHT + 1}" y="0" width="{RIGHT}" height="{H}" fill="{t["bg"]}"/>')
    out.append(f'<rect x="0" y="0" width="{W}" height="{TOP - 10}" fill="{t["bg"]}"/>')
    out.append(f'<rect x="0" y="{BASELINE_Y + 10}" width="{W}" height="{H - BASELINE_Y - 10}" fill="{t["bg"]}"/>')
    out.append(f'<line x1="{LEFT}" y1="{BASELINE_Y}" x2="{W - RIGHT}" y2="{BASELINE_Y}" stroke="{t["axis"]}" stroke-width="1"/>')

    # month labels, spaced to avoid overlap
    last_x = -999
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        if dt.day == 1 and xs[i] - last_x > 44:
            out.append(f'<text x="{xs[i]}" y="{H - 8}">{MONTHS[dt.month - 1]}</text>')
            last_x = xs[i]

    # stems + event nodes for the busiest days
    order = sorted(range(n), key=lambda i: counts[i], reverse=True)
    picked, used_x = [], []
    for i in order:
        if counts[i] <= 0:
            break
        if all(abs(xs[i] - ux) > 18 for ux in used_x):
            picked.append(i)
            used_x.append(xs[i])
        if len(picked) >= TOP_N:
            break
    for rank, i in enumerate(sorted(picked, key=lambda i: xs[i])):
        out.append(f'<line x1="{xs[i]:.1f}" y1="{ys[i]:.1f}" x2="{xs[i]:.1f}" y2="{BASELINE_Y}" '
                    f'stroke="{t["stem"]}" stroke-width="1"/>')
        out.append(f'<circle class="node" cx="{xs[i]:.1f}" cy="{ys[i]:.1f}" r="3.4" fill="{t["node"]}">'
                    f'<title>{days[i]["date"]}: {counts[i]} contributions</title></circle>')
        if rank < 3:
            out.append(f'<text x="{xs[i]:.1f}" y="{max(ys[i] - 8, 10):.1f}" text-anchor="middle" '
                        f'fill="{t["strong"]}">{counts[i]}</text>')

    # the worldline itself, drawn last so it sits above the grid/stems
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    out.append(f'<polyline class="trail" points="{pts}" fill="none" stroke="url(#g-{theme})" '
                f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round" filter="url(#f-{theme})"/>')

    total = f'{cal["totalContributions"]:,}'
    out.append(f'<text x="{LEFT}" y="20"><tspan style="fill:{t["strong"]};font-weight:bold">{total}</tspan>'
                f' contributions &#183; <tspan style="fill:{t["strong"]};font-weight:bold">{active}</tspan> active days'
                f' &#183; one worldline</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    src, out_dir = sys.argv[1], Path(sys.argv[2])
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (out_dir / f"worldline-{theme}.svg").write_text(draw(cal, theme), encoding="utf-8")
        print("wrote", out_dir / f"worldline-{theme}.svg")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        import xml.etree.ElementTree as ET

        assert amp_for(0, 100) == 0
        assert amp_for(100, 100) == MAX_AMP
        assert 0 < amp_for(1, 100) < amp_for(50, 100) < amp_for(100, 100)

        cal = {
            "totalContributions": 7,
            "weeks": [
                {"contributionDays": [{"date": "2026-01-01", "contributionCount": 0},
                                       {"date": "2026-01-02", "contributionCount": 5}]},
                {"contributionDays": [{"date": "2026-01-03", "contributionCount": 2},
                                       {"date": "2026-02-01", "contributionCount": 0}]},
            ],
        }
        for theme in THEMES:
            svg = draw(cal, theme)
            ET.fromstring(svg)  # raises if not well-formed XML
            assert svg.count("<circle") == 2  # two nonzero days -> two event nodes
            assert "7" in svg and "contributions" in svg
            assert len(svg.encode("utf-8")) < 120_000
        print("self-check ok")
    else:
        main()
