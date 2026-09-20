import os
import requests

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/languages-5-equal-v2.svg"

WIDTH = 500
HEIGHT = 220

BG = "#0d1117"
BORDER = "#30363d"
TITLE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#9da7b3"

LANG_COLORS = {
    "CSS": "#a855f7",
    "C++": "#ff4d94",
    "JavaScript": "#f6e05e",
    "Python": "#4aa8ff",
    "PowerShell": "#0058b8",
    "Lua": "#2ea44f",
    "Shell": "#ff812d",
    "TypeScript": "#16c6c8",
}

DISPLAY_ORDER = [
    "CSS",
    "C++",
    "JavaScript",
    "Python",
    "PowerShell",
    "Lua",
    "Shell",
    "TypeScript",
]

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required")


def graphql(query, variables=None):
    response = requests.post(
        "https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    return data["data"]


query = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(
      first: 100
      after: $after
      ownerAffiliations: OWNER
      isFork: false
      privacy: PUBLIC
      orderBy: {field: PUSHED_AT, direction: DESC}
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""

language_sizes = {}
after = None

while True:
    data = graphql(query, {"login": USERNAME, "after": after})
    repos = data["user"]["repositories"]["nodes"]

    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size = edge["size"]
            language_sizes[name] = language_sizes.get(name, 0) + size

    page_info = data["user"]["repositories"]["pageInfo"]
    if not page_info["hasNextPage"]:
        break

    after = page_info["endCursor"]

if not language_sizes:
    language_sizes = {
        "CSS": 1,
        "C++": 1,
        "JavaScript": 1,
        "Python": 1,
        "PowerShell": 1,
        "Lua": 1,
        "Shell": 1,
        "TypeScript": 1,
    }

items = []
for name in DISPLAY_ORDER:
    size = language_sizes.get(name, 0)
    items.append(
        {
            "name": name,
            "size": size,
            "color": LANG_COLORS.get(name, "#58a6ff"),
        }
    )

total = sum(item["size"] for item in items)
if total == 0:
    total = 1

for item in items:
    item["percent"] = item["size"] / total * 100

card_x = 12
card_y = 16
card_w = WIDTH - 24
card_h = HEIGHT - 32

bar_margin = 28
bar_h = 8

content_height = 140
content_top = card_y + (card_h - content_height) / 2

title_y = content_top + 16
bar_y = content_top + 38

bar_x = card_x + bar_margin
bar_w = card_w - (bar_margin * 2)

segment_w = bar_w / len(items)

bar_segments = []
for i, item in enumerate(items):
    x = bar_x + segment_w * i

    if i == 0:
        path = (
            f"M{x + 4:.2f},{bar_y:.2f} "
            f"H{x + segment_w:.2f} "
            f"V{bar_y + bar_h:.2f} "
            f"H{x + 4:.2f} "
            f"Q{x:.2f},{bar_y + bar_h:.2f} {x:.2f},{bar_y + bar_h - 4:.2f} "
            f"V{bar_y + 4:.2f} "
            f"Q{x:.2f},{bar_y:.2f} {x + 4:.2f},{bar_y:.2f} Z"
        )
        bar_segments.append(f'<path d="{path}" fill="{item["color"]}"/>')
    elif i == len(items) - 1:
        x2 = x + segment_w
        path = (
            f"M{x:.2f},{bar_y:.2f} "
            f"H{x2 - 4:.2f} "
            f"Q{x2:.2f},{bar_y:.2f} {x2:.2f},{bar_y + 4:.2f} "
            f"V{bar_y + bar_h - 4:.2f} "
            f"Q{x2:.2f},{bar_y + bar_h:.2f} {x2 - 4:.2f},{bar_y + bar_h:.2f} "
            f"H{x:.2f} Z"
        )
        bar_segments.append(f'<path d="{path}" fill="{item["color"]}"/>')
    else:
        bar_segments.append(
            f'<rect x="{x:.2f}" y="{bar_y:.2f}" width="{segment_w:.2f}" height="{bar_h}" fill="{item["color"]}"/>'
        )

# 4 colonnes × 2 lignes
col_centers = [
    card_x + card_w * 0.16,
    card_x + card_w * 0.36,
    card_x + card_w * 0.58,
    card_x + card_w * 0.81,
]

row1_dot_y = content_top + 70
row1_label_y = content_top + 74
row1_percent_y = content_top + 90

row2_dot_y = content_top + 108
row2_label_y = content_top + 112
row2_percent_y = content_top + 128

dot_radius = 5

dots = []
labels = []
percents = []

for i, item in enumerate(items):
    col = i % 4
    row = i // 4

    cx = col_centers[col]

    if row == 0:
        dot_y = row1_dot_y
        label_y = row1_label_y
        percent_y = row1_percent_y
    else:
        dot_y = row2_dot_y
        label_y = row2_label_y
        percent_y = row2_percent_y

    dots.append(
        f'<circle cx="{cx - 34:.2f}" cy="{dot_y:.2f}" r="{dot_radius}" fill="{item["color"]}"/>'
    )

    labels.append(
        f'<text x="{cx:.2f}" y="{label_y:.2f}" text-anchor="middle" fill="{TEXT}" font-size="10.5" font-family="Segoe UI, Arial, sans-serif">{item["name"]}</text>'
    )

    percents.append(
        f'<text x="{cx:.2f}" y="{percent_y:.2f}" text-anchor="middle" fill="{MUTED}" font-size="9.5" font-family="Segoe UI, Arial, sans-serif">{item["percent"]:.2f}%</text>'
    )

svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
    <rect
        x="{card_x}"
        y="{card_y}"
        width="{card_w}"
        height="{card_h}"
        rx="6"
        fill="{BG}"
        stroke="{BORDER}"
    />

    <text
        x="{WIDTH / 2:.2f}"
        y="{title_y:.2f}"
        text-anchor="middle"
        fill="{TITLE}"
        font-size="19"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >Top Languages</text>

    {''.join(bar_segments)}
    {''.join(dots)}
    {''.join(labels)}
    {''.join(percents)}
</svg>
'''

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated {OUTPUT}")
