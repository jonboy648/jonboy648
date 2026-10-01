"""Write terminal-promo.svg: a looping, animated terminal that plays five
scenes (a quote, the agent team, the printer fleet, order flow, a name card).

Pure CSS animation inside one SVG, so GitHub shows it as an image with no
render step. Every element gets a visibility window [start, end) in seconds
within the loop; the helpers below turn windows into keyframes.

    python terminal_promo.py out.svg
"""
import sys

W, H = 1200, 600
LOOP = 25.0                      # seconds for the whole reel
SCENE = LOOP / 5                 # five scenes, equal length
FONT = "SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"
CHAR = 0.6                       # monospace advance, in em
C = {"bg": "#0B0E13", "panel": "#11161D", "line": "#222A35", "text": "#C9D1DB", "dim": "#6B7685",
     "accent": "#E0612B", "hot": "#FF8A57", "ok": "#4CC38A", "bad": "#E5534B", "blue": "#7AA2F7"}

css, body = [], []
_n = [0]


def pct(t):
    return f"{max(0.0, min(100.0, t / LOOP * 100)):.3f}%"


def window(start, end, fade=0.25):
    """A class that is visible from start to end, fading in and out."""
    _n[0] += 1
    k = f"w{_n[0]}"
    css.append(f"@keyframes {k}{{0%,{pct(start)}{{opacity:0}}{pct(start + fade)},{pct(end - fade)}{{opacity:1}}"
               f"{pct(end)},100%{{opacity:0}}}}.{k}{{opacity:0;animation:{k} {LOOP}s linear infinite}}")
    return k


def typed(x, y, text, start, end, size=26, color=None, prompt=True):
    """A command that types itself out, then holds until end."""
    chars = len(text)
    dur = min(1.4, 0.05 * chars + 0.3)
    width = chars * size * CHAR + 4
    _n[0] += 1
    k = f"t{_n[0]}"
    css.append(f"@keyframes {k}{{0%,{pct(start)}{{transform:translateX(0);animation-timing-function:steps({chars},end)}}"
               f"{pct(start + dur)}{{transform:translateX({width:.1f}px);opacity:1}}{pct(start + dur + 0.05)},100%{{transform:translateX({width:.1f}px);opacity:0}}}}"
               f".{k}{{animation:{k} {LOOP}s linear infinite}}")
    vis = window(start, end, fade=0.05)
    sign = f'<tspan fill="{C["accent"]}">$ </tspan>' if prompt else ""
    off = 2 * size * CHAR if prompt else 0
    body.append(f'<g class="{vis}"><text x="{x}" y="{y}" font-size="{size}" fill="{color or C["text"]}">{sign}{esc(text)}</text>'
                f'<rect class="{k}" x="{x + off:.1f}" y="{y - size}" width="{width:.1f}" height="{size * 1.35:.1f}" fill="{C["bg"]}"/></g>')
    return start + dur


def show(svg, start, end, fade=0.25):
    body.append(f'<g class="{window(start, end, fade)}">{svg}</g>')


def grow(svg_shape, start, end, origin="0% 50%", axis="X"):
    """A shape that scales in from 0 along one axis, then holds."""
    _n[0] += 1
    k = f"g{_n[0]}"
    css.append(f"@keyframes {k}{{0%,{pct(start)}{{transform:scale{axis}(0)}}{pct(start + 0.9)},100%{{transform:scale{axis}(1)}}}}"
               f".{k}{{transform-box:fill-box;transform-origin:{origin};animation:{k} {LOOP}s ease-out infinite}}")
    show(svg_shape.replace("<rect ", f'<rect class="{k}" ', 1), start, end, fade=0.05)


def draw_line(x1, y1, x2, y2, start, end, color):
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    _n[0] += 1
    k = f"d{_n[0]}"
    css.append(f"@keyframes {k}{{0%,{pct(start)}{{stroke-dashoffset:{length:.1f}}}{pct(start + 0.6)},100%{{stroke-dashoffset:0}}}}"
               f".{k}{{stroke-dasharray:{length:.1f};animation:{k} {LOOP}s ease-out infinite}}")
    show(f'<line class="{k}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>', start, end, fade=0.05)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=22, color=None, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color or C["text"]}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def caption(label, start, end):
    show(text(70, H - 34, label, 16, C["dim"]), start, end)


X0, Y0 = 90, 150

# 1. quoting
s, e = 0.0, SCENE
caption("quoting", s, e)
t = typed(X0, Y0, "vault quote --part bracket.stl", s + 0.3, e)
for i, (k, v, col) in enumerate([("analyzing mesh", "ok", C["ok"]), ("material", "PETG, 0.20 mm layers", None),
                                 ("print time", "2 h 41 m on the X1C", None), ("status", "quoted, ready to schedule", C["ok"])]):
    y = Y0 + 62 + i * 44
    show(text(X0 + 30, y, k, 22, C["dim"]) + text(X0 + 330, y, v, 22, col), t + 0.25 + i * 0.35, e)

# 2. the agent team
s, e = SCENE, 2 * SCENE
caption("agent team", s, e)
t = typed(X0, Y0, "mesh status", s + 0.3, e)
cx, cy = 600, 340
roles = ["orders", "quoting", "printers", "books", "shipping", "design"]
spots = [(330, 250), (600, 220), (870, 250), (330, 440), (600, 470), (870, 440)]
for i, ((x, y), role) in enumerate(zip(spots, roles)):
    at = t + 0.2 + i * 0.22
    draw_line(cx, cy, x, y, at, e, C["line"])
    show(f'<rect x="{x - 78}" y="{y - 24}" width="156" height="46" rx="8" fill="{C["panel"]}" stroke="{C["line"]}"/>'
         f'<circle cx="{x - 56}" cy="{y - 1}" r="6" fill="{C["ok"]}"/>' + text(x - 40, y + 7, role, 20), at + 0.4, e)
show(f'<rect x="{cx - 92}" y="{cy - 28}" width="184" height="54" rx="10" fill="{C["panel"]}" stroke="{C["accent"]}" stroke-width="2"/>'
     + text(cx, cy + 8, "claude-lead", 22, C["hot"], "bold", "middle"), t + 0.1, e)
show(text(X0, H - 80, "agents online across 7 machines", 20, C["dim"]), t + 1.9, e)

# 3. the printer fleet
s, e = 2 * SCENE, 3 * SCENE
caption("print fleet", s, e)
t = typed(X0, Y0, "fleet", s + 0.3, e)
fleet = [("X1C", "bracket x12", 0.78, "78%"), ("H2D", "ear tags x40", 0.41, "41%"),
         ("Fuse 1+", "nylon clips", 0.12, "12%"), ("Phrozen", "resin bank", 1.0, "done")]
for i, (name, job, p, label) in enumerate(fleet):
    y = Y0 + 70 + i * 70
    at = t + 0.2 + i * 0.3
    show(text(X0 + 30, y, name, 22, C["text"], "bold") + text(X0 + 190, y, job, 20, C["dim"])
         + f'<rect x="{X0 + 420}" y="{y - 18}" width="480" height="20" rx="4" fill="{C["panel"]}" stroke="{C["line"]}"/>'
         + text(X0 + 930, y, label, 20, C["ok"] if p >= 1 else C["text"]), at, e)
    grow(f'<rect x="{X0 + 422}" y="{y - 16}" width="{476 * p:.0f}" height="16" rx="3" fill="{C["ok"] if p >= 1 else C["accent"]}"/>',
         at + 0.2, e)

# 4. order flow
s, e = 3 * SCENE, 4 * SCENE
caption("order flow", s, e)
t = typed(X0, Y0, "orderflow --instrument MGC", s + 0.3, e)
closes = [52, 55, 53, 58, 61, 59, 64, 62, 66, 70, 68, 73, 71, 76, 79]
deltas = [3, 5, -2, 7, 6, -3, 8, -2, 6, 9, -4, 8, -3, 7, 9]
px, base, step = X0 + 40, 420, 56
prev = 50
for i, (c, d) in enumerate(zip(closes, deltas)):
    up = c >= prev
    yc = lambda v: 420 - (v - 50) * 6.6
    top, bot = yc(max(c, prev)), yc(min(c, prev))
    x = px + i * step
    col = C["ok"] if up else C["bad"]
    at = t + 0.15 + i * 0.12
    show(f'<line x1="{x + 14}" y1="{top - 10:.0f}" x2="{x + 14}" y2="{bot + 10:.0f}" stroke="{col}" stroke-width="2"/>'
         f'<rect x="{x + 4}" y="{top:.0f}" width="20" height="{max(4, bot - top):.0f}" fill="{col}" rx="2"/>', at, e, fade=0.1)
    h = abs(d) * 4
    dcol = C["ok"] if d >= 0 else C["bad"]
    # positive delta grows up from the zero line, negative grows down from it
    grow(f'<rect x="{x + 4}" y="{490 - h if d >= 0 else 490}" width="20" height="{h}" fill="{dcol}" opacity="0.7"/>',
         at, e, origin="50% 100%" if d >= 0 else "50% 0%", axis="Y")
    prev = c
show(text(px, 532, "cumulative delta", 16, C["dim"]), t + 0.4, e)

# 5. name card
s, e = 4 * SCENE, LOOP
show(text(W / 2, 270, "Jon Cackler", 64, "#E6EAF0", "bold", "middle"), s + 0.3, e - 0.2)
show(text(W / 2, 322, "Variety Vault 3D · Ames, Iowa", 26, C["accent"], "bold", "middle"), s + 0.7, e - 0.2)
show(text(W / 2, 366, "AI agents · 3D printing · order-flow tools", 22, C["dim"], "normal", "middle"), s + 1.1, e - 0.2)
show(text(W / 2, 430, "github.com/jonboy648  ·  vaultshop.us", 20, C["text"], "normal", "middle"), s + 1.5, e - 0.2)
caption("open channel", s, e)

frame = (f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>'
         f'<rect width="{W}" height="{H}" fill="url(#scan)"/>'
         f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" rx="14" fill="none" stroke="{C["line"]}"/>'
         f'<circle cx="52" cy="52" r="7" fill="{C["bad"]}"/><circle cx="76" cy="52" r="7" fill="#E3B341"/>'
         f'<circle cx="100" cy="52" r="7" fill="{C["ok"]}"/>'
         + text(W / 2, 58, "vault@shop: ~", 16, C["dim"], "normal", "middle")
         + f'<line x1="20" y1="80" x2="{W - 20}" y2="80" stroke="{C["line"]}"/>'
         + text(W - 70, H - 34, "vaultshop.us", 16, C["dim"], "normal", "end"))


def build():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Jon Cackler, Variety Vault 3D: a terminal showing quoting, the agent team, the print fleet and order flow">'
            f'<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#FFFFFF" opacity="0.025"/></pattern></defs>'
            f'<style>text{{font-family:{FONT}}}{"".join(css)}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important;transform:none!important}}}}</style>'
            f'{frame}{"".join(body)}</svg>')


if __name__ == "__main__":
    svg = build()
    assert svg.count("<svg") == 1 and "Jon Cackler" in svg
    assert all(0 <= float(p[:-1]) <= 100 for p in __import__("re").findall(r"\d+\.\d+%", svg))
    open(sys.argv[1] if len(sys.argv) > 1 else "terminal-promo.svg", "w", encoding="utf-8").write(svg)
    print(f"ok, {len(svg)} bytes, {_n[0]} animated parts")
