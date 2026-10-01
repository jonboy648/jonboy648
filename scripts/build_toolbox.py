"""Draw the toolbox as two themed SVGs from the brand logos in assets/logos.

    python3 scripts/build_toolbox.py           # self-check
    python3 scripts/build_toolbox.py build     # write assets/toolbox-{dark,light}.svg

Logos come from svgl.app (Arduino and Bambu Lab from Simple Icons). Each one is
embedded as a data URI so its ids can't collide with another logo's.
"""
import base64, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGOS = ROOT / "assets" / "logos"
GROUPS = [
    ("Languages", [("python", "Python"), ("rust", "Rust"), ("csharp", "C#"), ("typescript", "TypeScript"),
                   ("cpp", "C++"), ("powershell", "PowerShell"), ("bash", "Bash")]),
    ("Web and data", [("react", "React"), ("vite", "Vite"), ("tailwind", "Tailwind"), ("nodejs", "Node.js"),
                      ("fastapi", "FastAPI"), ("postgresql", "Postgres"), ("cloudflare", "Cloudflare")]),
    ("Agents and automation", [("claude", "Claude"), ("openai", "OpenAI"), ("github", "GitHub")]),
    ("Hardware and making", [("raspberrypi", "Raspberry Pi"), ("arduino", "Arduino"), ("bambulab", "Bambu Lab"),
                             ("blender", "Blender")]),
]
MONO = {"arduino": "#00878F", "bambulab": "#00AE42"}  # Simple Icons ship without a fill
THEME = {
    "dark": dict(card="#161B22", edge="#30363D", tile="#0D1117", tile_edge="#262C36", title="#30D6C8", label="#9198A1"),
    "light": dict(card="#F6F8FA", edge="#D0D7DE", tile="#FFFFFF", tile_edge="#D8DEE4", title="#0E9488", label="#59636E"),
}
W, CARD_W, CARD_H, GAP, SLOT, TILE, ICON = 840, 410, 118, 20, 56, 44, 26


def logo(slug, mode):
    path = LOGOS / f"{slug}-{mode}.svg"
    raw = (path if path.exists() else LOGOS / f"{slug}-light.svg").read_text(encoding="utf-8")
    if slug in MONO:
        raw = raw.replace("<svg ", f'<svg fill="{MONO[slug]}" ', 1)
    return "data:image/svg+xml;base64," + base64.b64encode(raw.encode()).decode()


def draw(mode):
    t = THEME[mode]
    h = 2 * CARD_H + GAP
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="Toolbox">',
           "<style>.t{font:600 11px Consolas,Menlo,monospace;letter-spacing:2px}.l{font:10px 'Segoe UI',Helvetica,Arial,sans-serif}"
           "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
           ".i{opacity:0;animation:rise .5s ease-out forwards}"
           "@media (prefers-reduced-motion:reduce){.i{opacity:1;animation:none}}</style>"]
    n = 0
    for g, (title, items) in enumerate(GROUPS):
        x, y = (g % 2) * (CARD_W + GAP), (g // 2) * (CARD_H + GAP)
        out.append(f'<rect x="{x + .5}" y="{y + .5}" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="12" fill="{t["card"]}" stroke="{t["edge"]}"/>')
        out.append(f'<text class="t" x="{x + 18}" y="{y + 27}" fill="{t["title"]}">{title.upper()}</text>')
        start = x + (CARD_W - (len(items) * SLOT - (SLOT - TILE))) / 2
        for k, (slug, name) in enumerate(items):
            tx, ty = start + k * SLOT, y + 40
            out.append(f'<g class="i" style="animation-delay:{n * 45}ms">'
                       f'<rect x="{tx + .5}" y="{ty + .5}" width="{TILE - 1}" height="{TILE - 1}" rx="10" fill="{t["tile"]}" stroke="{t["tile_edge"]}"/>'
                       f'<image x="{tx + (TILE - ICON) / 2}" y="{ty + (TILE - ICON) / 2}" width="{ICON}" height="{ICON}" href="{logo(slug, mode)}"/>'
                       f'<text class="l" x="{tx + TILE / 2}" y="{ty + TILE + 16}" text-anchor="middle" fill="{t["label"]}">{name}</text></g>')
            n += 1
    out.append("</svg>")
    return "".join(out)


def check():
    slugs = [s for _, items in GROUPS for s, _ in items]
    assert len(slugs) == len(set(slugs))
    for s in slugs:
        assert (LOGOS / f"{s}-light.svg").exists(), s
    for g, (_, items) in enumerate(GROUPS):
        assert len(items) * SLOT - (SLOT - TILE) <= CARD_W - 24, f"group {g} overflows its card"
    for mode in THEME:
        svg = draw(mode)
        ET.fromstring(svg)
        assert svg.count("<image") == len(slugs)
        assert len(svg) < 160_000, len(svg)
    print(f"OK: {len(slugs)} logos in {len(GROUPS)} groups, both themes parse")


if __name__ == "__main__":
    check()
    if sys.argv[1:] == ["build"]:
        for mode in THEME:
            (ROOT / "assets" / f"toolbox-{mode}.svg").write_text(draw(mode), encoding="utf-8")
        print("wrote assets/toolbox-dark.svg and assets/toolbox-light.svg")
