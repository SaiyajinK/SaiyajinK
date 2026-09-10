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
    "C#": "#8b5cf6",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "XAML": "#6ea8fe",
    "Batchfile": "#6b7280",
    "Shell": "#89e051",
}

PREFERRED_ORDER = [
    "CSS",
    "C++",
    "JavaScript",
    "Python",
    "PowerShell",
    "C#",
    "TypeScript",
    "HTML",
    "XAML",
    "Shell",
    "Batchfile",
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
    }

selected = []

for name in PREFERRED_ORDER:
    if name in language_sizes:
        selected.append((name, language_sizes[name]))

if len(selected) < 5:
    remaining = sorted(
        [(k, v) for k, v in language_sizes.items() if k not in {n for n, _ in selected}],
        key=lambda x: x[1],
        reverse=True,
    )
    selected.extend(remaining[: 5 - len(selected)])

selected = selected[:5]

total = sum(size for _, size in selected)
if total == 0:
    total = 1

items = []
for name, size in selected:
    percent = size / total * 100
    items.append(
        {
            "name": name,
            "size": size,
            "percent": percent,
            "color": LANG_COLORS.get(name, "#58a6ff"),
        }
    )

card_x = 12
card_y = 16
card_w = WIDTH - 24
card_h = HEIGHT - 32

bar_margin = 28
bar_h = 8

content_height = 124
content_top = card_y + (card_h - content_height) / 2

title_y = content_top + 18
bar_y = content_top + 40
dot_y = content_top + 68
label_y = content_top + 91
percent_y = content_top + 116

bar_x = card_x + bar_margin
bar_w = card_w - (bar_margin * 2)

segment_w = bar_w / len(items)
centers = [bar_x + segment_w * i + segment_w / 2 for i in range(len(items))]

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

dots = []
labels = []
percents = []

for i, item in enumerate(items):
    cx = centers[i]
    dots.append(f'<circle cx="{cx:.2f}" cy="{dot_y:.2f}" r="3" fill="{item["color"]}"/>')
    labels.append(
        f'<text x="{cx:.2f}" y="{label_y:.2f}" text-anchor="middle" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">{item["name"]}</text>'
    )
    percents.append(
        f'<text x="{cx:.2f}" y="{percent_y:.2f}" text-anchor="middle" fill="{MUTED}" font-size="10" font-family="Segoe UI, Arial, sans-serif">{item["percent"]:.2f}%</text>'
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
