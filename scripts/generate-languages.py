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


# 5 langages les plus utilisés
languages = sorted(
    languages.items(),
    key=lambda x: x[1],
    reverse=True
)[:5]

total = sum(amount for _, amount in languages)

colors = {
    "CSS": "#663399",
    "C++": "#f34b7d",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "PowerShell": "#012456",
    "HTML": "#e34c26",
    "CMake": "#DA3434"
}


WIDTH = 500
HEIGHT = 110

BAR_X = 24
BAR_Y = 42
BAR_WIDTH = 452
BAR_HEIGHT = 12

SEGMENT_COUNT = len(languages)
SEGMENT_WIDTH = BAR_WIDTH / SEGMENT_COUNT


svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<style>
.title {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 18px;
    font-weight: 600;
    fill: #2f81f7;
}}

.legend {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 10px;
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


# 5 portions visuellement égales
for index, (language, amount) in enumerate(languages):

    x = BAR_X + index * SEGMENT_WIDTH
    color = colors.get(language, "#8b949e")

    svg += f"""
<rect
    x="{x:.2f}"
    y="{BAR_Y}"
    width="{SEGMENT_WIDTH:.2f}"
    height="{BAR_HEIGHT}"
    fill="{color}"
/>
"""


svg += """
</g>
"""


# Labels centrés sous CHAQUE segment
LEGEND_Y = 80

for index, (language, amount) in enumerate(languages):

    percent = (amount / total * 100) if total else 0
    color = colors.get(language, "#8b949e")

    center_x = (
        BAR_X
        + index * SEGMENT_WIDTH
        + SEGMENT_WIDTH / 2
    )

    label = f"{language} {percent:.1f}%"

    svg += f"""
<g>
    <circle
        cx="{center_x - 22:.2f}"
        cy="{LEGEND_Y - 3}"
        r="3.5"
        fill="{color}"
    />

    <text
        x="{center_x + 3:.2f}"
        y="{LEGEND_Y}"
        text-anchor="middle"
        dominant-baseline="middle"
        class="legend"
    >{label}</text>
</g>
"""


svg += """
</svg>
"""


output_dir = "profile-summary-card-output/custom"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(
    output_dir,
    "top-languages-equal.svg"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:
    file.write(svg)

print(f"Generated: {output_file}")
