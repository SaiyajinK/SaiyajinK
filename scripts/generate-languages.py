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

# Garde les 4 langages les plus utilisés
languages = sorted(
    languages.items(),
    key=lambda x: x[1],
    reverse=True
)[:4]

total = sum(amount for _, amount in languages)

colors = {
    "CSS": "#663399",
    "JavaScript": "#f1e05a",
    "PowerShell": "#012456",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CMake": "#DA3434"
}

width = 500
height = 105

bar_x = 24
bar_y = 42
bar_width = 452
bar_height = 12

svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}">

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
    width="{width - 1}"
    height="{height - 1}"
    rx="6"
    fill="#0d1117"
    stroke="#30363d"
/>

<text
    x="24"
    y="26"
    class="title"
>Top Languages</text>

<clipPath id="barClip">
    <rect
        x="{bar_x}"
        y="{bar_y}"
        width="{bar_width}"
        height="{bar_height}"
        rx="6"
    />
</clipPath>

<g clip-path="url(#barClip)">
"""

# IMPORTANT :
# La barre est divisée en 4 portions VISUELLEMENT ÉGALES.
# Les vrais pourcentages sont affichés seulement dans la légende.
segment_width = bar_width / 4

for index, (language, amount) in enumerate(languages):
    color = colors.get(language, "#8b949e")
    current_x = bar_x + (index * segment_width)

    svg += f"""
<rect
    x="{current_x:.2f}"
    y="{bar_y}"
    width="{segment_width:.2f}"
    height="{bar_height}"
    fill="{color}"
/>
"""

svg += """
</g>
"""

# Légende sur une seule ligne sous la barre
legend_y = 79
legend_x = 24

for language, amount in languages:
    percent = (amount / total * 100) if total else 0
    color = colors.get(language, "#8b949e")

    label = f"{language} {percent:.1f}%"

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

    legend_x += 22 + len(label) * 6.2

svg += """
</svg>
"""

output_dir = "profile-summary-card-output/custom"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(
    output_dir,
    "top-languages-horizontal.svg"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:
    file.write(svg)

print(f"Generated: {output_file}")
