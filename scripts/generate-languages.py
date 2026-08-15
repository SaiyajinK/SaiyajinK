import os
import requests

USERNAME = "SaiyajinK"
TOKEN = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

repos = requests.get(
    f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner",
    headers=headers
).json()

languages = {}

for repo in repos:
    if repo.get("fork"):
        continue

    data = requests.get(
        repo["languages_url"],
        headers=headers
    ).json()

    for language, amount in data.items():
        languages[language] = languages.get(language, 0) + amount

languages = sorted(
    languages.items(),
    key=lambda x: x[1],
    reverse=True
)[:4]

total = sum(amount for _, amount in languages)

colors = {
    "CSS": "#663399",
    "C++": "#f34b7d",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "PowerShell": "#012456",
    "HTML": "#e34c26"
}

WIDTH = 500
HEIGHT = 105

BAR_X = 24
BAR_Y = 42
BAR_WIDTH = 452
BAR_HEIGHT = 12

SEGMENT_WIDTH = BAR_WIDTH / 4

svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<style>
.title {{
    font: 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    fill: #2f81f7;
}}

.legend {{
    font: 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    fill: #8b949e;
}}
</style>

<rect
    x="0.5"
    y="0.5"
    width="{WIDTH - 1}"
    height="{HEIGHT - 1}"
    rx="6"
    fill="#0d1117"
    stroke="#30363d"
/>

<text
    x="{WIDTH / 2}"
    y="26"
    text-anchor="middle"
    class="title"
>Top Languages</text>

<clipPath id="clip">
    <rect
        x="{BAR_X}"
        y="{BAR_Y}"
        width="{BAR_WIDTH}"
        height="{BAR_HEIGHT}"
        rx="6"
    />
</clipPath>

<g clip-path="url(#clip)">
"""

for index, (language, amount) in enumerate(languages):
    x = BAR_X + (index * SEGMENT_WIDTH)
    color = colors.get(language, "#8b949e")

    svg += f"""
<rect
    x="{x}"
    y="{BAR_Y}"
    width="{SEGMENT_WIDTH}"
    height="{BAR_HEIGHT}"
    fill="{color}"
/>
"""

svg += """
</g>
"""

# Prépare les labels
labels = []

for language, amount in languages:
    percent = amount / total * 100 if total else 0
    label = f"{language} {percent:.1f}%"
    labels.append((language, label))

# Largeur approximative de chaque élément de légende
item_widths = []

for language, label in labels:
    item_width = 18 + len(label) * 6.2
    item_widths.append(item_width)

gap = 18
total_legend_width = sum(item_widths) + gap * (len(labels) - 1)

# Départ calculé pour centrer l'ensemble
legend_x = (WIDTH - total_legend_width) / 2
legend_y = 79

for index, (language, label) in enumerate(labels):
    color = colors.get(language, "#8b949e")

    svg += f"""
<circle
    cx="{legend_x + 4}"
    cy="{legend_y - 4}"
    r="4"
    fill="{color}"
/>

<text
    x="{legend_x + 12}"
    y="{legend_y}"
    class="legend"
>{label}</text>
"""

    legend_x += item_widths[index] + gap

svg += """
</svg>
"""

output_dir = "profile-summary-card-output/custom"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(
    output_dir,
    "top-languages-equal.svg"
)

with open(output_file, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated: {output_file}")
