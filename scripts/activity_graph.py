"""Gera assets/activity-{dark,light}.svg com as contribuições dos últimos 31 dias.

Uso: GITHUB_TOKEN=... python scripts/activity_graph.py <usuario>
"""
import datetime as dt
import json
import os
import sys
import urllib.request

USER = sys.argv[1]
DAYS = 31
W, H, PAD_L, PAD_R, PAD_T, PAD_B = 840, 300, 48, 20, 48, 40
THEMES = {
    "dark": {"bg": "#161b22", "fg": "#e6edf3", "muted": "#7d8590", "grid": "#21262d", "line": "#58a6ff"},
    "light": {"bg": "#f6f8fa", "fg": "#1f2328", "muted": "#656d76", "grid": "#d8dee4", "line": "#0969da"},
}


def fetch():
    end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    start = end - dt.timedelta(days=DAYS - 1)
    query = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    body = json.dumps({"query": query, "variables": {"u": USER, "f": start.isoformat(), "t": end.isoformat()}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body,
                                 {"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": USER})
    weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def svg(days, t):
    counts = [d["contributionCount"] for d in days]
    top = max(max(counts), 4)
    step = -(-top // 4)
    top = step * 4
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    x = lambda i: PAD_L + pw * i / (len(days) - 1)
    y = lambda v: PAD_T + ph * (1 - v / top)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" rx="8" fill="{t["bg"]}"/>',
           f'<text x="{W / 2}" y="28" fill="{t["fg"]}" font-size="15" font-weight="600" text-anchor="middle">{USER} · contributions, last {DAYS} days</text>']
    for k in range(5):
        v = step * k
        out.append(f'<line x1="{PAD_L}" x2="{W - PAD_R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{t["grid"]}"/>')
        out.append(f'<text x="{PAD_L - 8}" y="{y(v) + 4:.1f}" fill="{t["muted"]}" font-size="11" text-anchor="end">{v}</text>')
    for i, d in enumerate(days):
        if i % 5 == 0 or i == len(days) - 1:
            out.append(f'<text x="{x(i):.1f}" y="{H - 16}" fill="{t["muted"]}" font-size="11" text-anchor="middle">{d["date"][8:]}/{d["date"][5:7]}</text>')
    pts = " ".join(f"{x(i):.1f},{y(c):.1f}" for i, c in enumerate(counts))
    area = f"{x(0):.1f},{y(0):.1f} {pts} {x(len(days) - 1):.1f},{y(0):.1f}"
    out.append(f'<polygon points="{area}" fill="{t["line"]}" fill-opacity="0.12"/>')
    out.append(f'<polyline points="{pts}" fill="none" stroke="{t["line"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    out += [f'<circle cx="{x(i):.1f}" cy="{y(c):.1f}" r="3" fill="{t["line"]}"/>' for i, c in enumerate(counts)]
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    days = fetch()
    for name, theme in THEMES.items():
        with open(f"assets/activity-{name}.svg", "w") as f:
            f.write(svg(days, theme))
    print(f"{len(days)} dias, total {sum(d['contributionCount'] for d in days)}")
