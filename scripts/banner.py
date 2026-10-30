"""Gera assets/banner.svg: Atlas no centro, ladeado por retângulos áureos cuja espiral se desenha em loop.

Uso: python scripts/banner.py
"""
import base64

W, H = 1900, 500
RW, RH, RY = 760, 470, 15  # retângulo áureo (760/470 ≈ φ)
GOLD, LINE = "#c9a227", "#8b949e"

img = base64.b64encode(open("assets/banner.jpg", "rb").read()).decode()
IW = round(534 / 933 * RH)


def golden(x, y, w, h, n=9):
    """Quadrados e arcos de um corte áureo, girando esquerda, topo, direita, base."""
    squares, arcs = [], []
    for i in range(n):
        d = i % 4
        s = h if d in (0, 2) else w
        if d == 0:
            squares.append((x, y, s)); arcs.append((x, y + s, x + s, y, s)); x += s; w -= s
        elif d == 1:
            squares.append((x, y, s)); arcs.append((x, y, x + s, y + s, s)); y += s; h -= s
        elif d == 2:
            squares.append((x + w - s, y, s)); arcs.append((x + w, y, x + w - s, y + s, s)); w -= s
        else:
            squares.append((x, y + h - s, s)); arcs.append((x + w, y + h, x, y + h - s, s)); h -= s
    spiral = f"M{arcs[0][0]:.1f},{arcs[0][1]:.1f} " + " ".join(
        f"A{r:.1f},{r:.1f} 0 0 1 {ex:.1f},{ey:.1f}" for _, _, ex, ey, r in arcs
    )
    return squares, spiral


squares, spiral = golden(0, 0, RW, RH)
lines = [f'<rect class="ln sq" pathLength="1" width="{RW}" height="{RH}" style="animation-delay:0s"/>']
lines += [
    f'<rect class="ln sq" pathLength="1" x="{x:.1f}" y="{y:.1f}" width="{s:.1f}" height="{s:.1f}" style="animation-delay:{0.25 * (i + 1):.2f}s"/>'
    for i, (x, y, s) in enumerate(squares)
]
lines.append(f'<path class="ln sp" pathLength="1" d="{spiral}" style="animation-delay:.6s"/>')
group = "\n    ".join(lines)

stars = [(120, 60), (330, 430), (610, 90), (1290, 70), (1560, 420), (1790, 120), (900, 40), (1010, 470)]
star_svg = "\n  ".join(
    f'<circle class="st" cx="{x}" cy="{y}" r="1.6" style="animation-delay:{i * 0.7:.1f}s"/>' for i, (x, y) in enumerate(stars)
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
  .ln {{ fill: none; stroke-width: 1.4; stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 14s ease-in-out infinite both; }}
  .sq {{ stroke: {LINE}; stroke-opacity: .45; }}
  .sp {{ stroke: {GOLD}; stroke-width: 2; animation-duration: 14s; }}
  .st {{ fill: #e6edf3; opacity: .15; animation: twinkle 4.2s ease-in-out infinite both; }}
  .glow {{ opacity: 0; animation: glow 7s ease-in-out infinite; }}
  @keyframes draw {{ 0% {{ stroke-dashoffset: 1; opacity: 1; }} 35%, 82% {{ stroke-dashoffset: 0; opacity: 1; }} 95%, 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
  @keyframes twinkle {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
  @keyframes glow {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: .55; }} }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ animation: none !important; }}
    .ln {{ stroke-dashoffset: 0; }}
  }}
</style>
<defs><filter id="blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter></defs>
<rect width="{W}" height="{H}" fill="#000"/>
  {star_svg}
<g transform="translate(40 {RY})">
    {group}
</g>
<g transform="translate({W - 40} {RY}) scale(-1 1)">
    {group}
</g>
<image class="glow" filter="url(#blur)" x="{(W - IW) / 2:.1f}" y="{RY}" width="{IW}" height="{RH}" xlink:href="data:image/jpeg;base64,{img}"/>
<image x="{(W - IW) / 2:.1f}" y="{RY}" width="{IW}" height="{RH}" xlink:href="data:image/jpeg;base64,{img}"/>
</svg>
"""
open("assets/banner.svg", "w").write(svg)
