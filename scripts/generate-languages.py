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

languages_data = {}

for repo in repos:
    if repo.get("fork"):
        continue

    data = requests.get(
        repo["languages_url"],
        headers=headers
    ).json()

    for language, amount in data.items():
        languages_data[language] = languages_data.get(language, 0) + amount


# Langages affichés, dans cet ordre
LANGUAGES = [
    "CSS",
    "C++",
    "JavaScript",
    "Python",
    "PowerShell"
]

COLORS = {
    "CSS": "#663399",
    "C++": "#f34b7d",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "PowerShell": "#012456"
}

total = sum(languages_data.values())

values = []

for language in LANGUAGES:
    amount = languages_data.get(language, 0)
    percent = (amount / total * 100) if total else 0
    values.append((language, percent))


WIDTH = 500
HEIGHT = 105

BAR_X = 24
BAR_Y = 42
BAR_WIDTH = 452
BAR_HEIGHT = 12

SEGMENT_WIDTH = BAR_WIDTH / 5


svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<style>
.title {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 18px;
    fill: #2f81f7;
}}

.legend {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 9px;
    fill: #8b949e;
}}
</style>

<rect
    x="0.5"
    y="0.5"
    width="499"
    height="104"
    rx="6"
    fill="#0d1117"
    stroke="#30363d"
/>

<text
    x="250"
    y="25"
    text-anchor="middle"
    class="title"
>Top Languages</text>

<clipPath id="barClip">
    <rect
        x="{BAR_X}"
        y="{BAR_Y}"
        width="{BAR_WIDTH}"
        height="{BAR_HEIGHT}"
        rx="6"
    />
</clipPath>

<g clip-path="url(#barClip)">
"""


# 5 segments STRICTEMENT égaux
for index, (language, percent) in enumerate(values):

    x = BAR_X + index * SEGMENT_WIDTH

    svg += f"""
<rect
    x="{x:.2f}"
    y="{BAR_Y}"
    width="{SEGMENT_WIDTH + 0.2:.2f}"
    height="{BAR_HEIGHT}"
    fill="{COLORS[language]}"
/>
"""


svg += """
</g>
"""


# Un label centré sous chaque segment
for index, (language, percent) in enumerate(values):

    center_x = BAR_X + (index + 0.5) * SEGMENT_WIDTH

    svg += f"""
<circle
    cx="{center_x:.2f}"
    cy="71"
    r="3"
    fill="{COLORS[language]}"
/>

<text
    x="{center_x:.2f}"
    y="86"
    text-anchor="middle"
    class="legend"
>{language} {percent:.1f}%</text>
"""


svg += """
</svg>
"""


output_dir = "profile-summary-card-output/custom"
os.makedirs(output_dir, exist_ok=True)

# NOUVEAU NOM => impossible de récupérer l'ancien SVG
output_file = os.path.join(
    output_dir,
    "languages-5-equal.svg"
)

with open(output_file, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated: {output_file}")
