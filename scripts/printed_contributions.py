"""Draw a GitHub contribution calendar as a 3D print: a nozzle sweeps left to
right and each week's column of days is laid down behind it.

Reads the calendar JSON from `gh api graphql` (or the same shape from the
GitHub API inside an Action) and writes printed-contributions-dark.svg and
printed-contributions-light.svg.

    python printed_contributions.py calendar.json out_dir
"""
import json
import sys
from datetime import date
from pathlib import Path

CELL, GAP, LEFT, TOP = 11, 3, 34, 46
THEMES = {
    "dark": {"empty": "#1B222C", "levels": ["#5A2A17", "#9A4120", "#D9582A", "#FF8A57"],
             "text": "#9198A1", "strong": "#E6EDF3", "nozzle": "#9AA6B4", "body": "#2A323D"},
    "light": {"empty": "#EBEEF1", "levels": ["#F6C9B3", "#EE9A73", "#D9582A", "#9E3511"],
              "text": "#59636E", "strong": "#1F2328", "nozzle": "#5B6675", "body": "#D5DBE2"},
}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
STEP = 0.07  # seconds between columns


def levels(counts):
    nonzero = sorted(c for c in counts if c)
    if not nonzero:
        return lambda c: 0
    q = [nonzero[int(len(nonzero) * f) - 1 if int(len(nonzero) * f) else 0] for f in (0.25, 0.5, 0.75)]
    return lambda c: 0 if c == 0 else 1 + sum(c > t for t in q)


def draw(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"]
    level = levels([d["contributionCount"] for w in weeks for d in w["contributionDays"]])
    width = LEFT + len(weeks) * (CELL + GAP) + 16
    height = TOP + 7 * (CELL + GAP) + 34
    sweep = len(weeks) * STEP
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'role="img" aria-label="{cal["totalContributions"]} contributions in the last year">',
           "<style>",
           ".col{opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:lay .35s ease-out forwards}",
           "@keyframes lay{from{opacity:0;transform:scaleY(.2)}to{opacity:1;transform:scaleY(1)}}",
           f".noz{{animation:sweep {sweep:.2f}s linear forwards}}",
           f"@keyframes sweep{{from{{transform:translateX(0)}}to{{transform:translateX({len(weeks) * (CELL + GAP)}px)}}}}",
           "@media (prefers-reduced-motion:reduce){.col{animation:none;opacity:1}.noz{animation:none}}",
           f"text{{font-family:Consolas,Menlo,monospace;font-size:10px;fill:{t['text']}}}",
           "</style>"]
    last_month = None
    for i, w in enumerate(weeks):
        x = LEFT + i * (CELL + GAP)
        month = int(w["contributionDays"][0]["date"][5:7])
        # label a month only if it runs at least three columns, so a partial first
        # month never prints on top of the next one ("SepOct")
        ahead = i + 2 < len(weeks) and int(weeks[i + 2]["contributionDays"][0]["date"][5:7]) == month
        if month != last_month and ahead:
            out.append(f'<text x="{x}" y="{TOP - 8}">{MONTHS[month - 1]}</text>')
            last_month = month
        out.append(f'<g class="col" style="animation-delay:{i * STEP:.2f}s">')
        for d in w["contributionDays"]:
            row = date.fromisoformat(d["date"]).isoweekday() % 7  # Sunday on top, like GitHub
            lv = level(d["contributionCount"])
            fill = t["empty"] if lv == 0 else t["levels"][lv - 1]
            out.append(f'<rect x="{x}" y="{TOP + row * (CELL + GAP)}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}">'
                       f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>')
        out.append("</g>")
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="2" y="{TOP + row * (CELL + GAP) + 9}">{name}</text>')
    # nozzle: a hot end that rides along the top edge as the columns go down
    nx = LEFT - 2
    out.append(f'<g class="noz"><rect x="{nx - 4}" y="6" width="22" height="12" rx="2" fill="{t["body"]}"/>'
               f'<path d="M{nx} 18 L{nx + 14} 18 L{nx + 9} 28 L{nx + 5} 28 Z" fill="{t["nozzle"]}"/>'
               f'<circle cx="{nx + 7}" cy="31" r="2.2" fill="{t["levels"][3]}"/></g>')
    total = f'{cal["totalContributions"]:,}'
    out.append(f'<text x="{LEFT}" y="{height - 10}"><tspan style="fill:{t["strong"]};font-weight:bold">{total}</tspan>'
               f' contributions in the last year, private work included</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    src, out_dir = sys.argv[1], Path(sys.argv[2])
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (out_dir / f"printed-contributions-{theme}.svg").write_text(draw(cal, theme), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # self-check: a tiny two-week calendar draws, and levels rank counts
        lv = levels([0, 1, 2, 3, 10])
        assert lv(0) == 0 and lv(1) == 1 and lv(10) == 4
        cal = {"totalContributions": 3, "weeks": [{"contributionDays": [{"date": "2026-09-20", "contributionCount": 1}]},
                                                    {"contributionDays": [{"date": "2026-09-27", "contributionCount": 2}]}]}
        svg = draw(cal, "dark")
        assert svg.count("<rect") == 2 + 1 and "3 contributions" in svg
        print("self-check ok")
    else:
        main()
