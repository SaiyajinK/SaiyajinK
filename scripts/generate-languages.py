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

    url = repo["languages_url"]
    data = requests.get(url, headers=headers).json()

    for language, amount in data.items():
        languages[language] = languages.get(language, 0) + amount

languages = dict(
    sorted(languages.items(), key=lambda x: x[1], reverse=True)[:6]
)

total = sum(languages.values())

colors = {
    "CSS": "#663399",
    "JavaScript": "#f1e05a",
    "PowerShell": "#012456",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "HTML": "#e34c26"
}

width = 600
height = 70 + len(languages) * 42

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<style>
.title {{
    font: 22px sans-serif;
    fill: #2f81f7;
}}
.label {{
    font: 14px sans-serif;
    fill: #8b949e;
}}
.percent {{
    font: 13px sans-serif;
    fill: #8b949e;
}}
</style>

<rect width="100%" height="100%" rx="6" fill="#0d1117" stroke="#30363d"/>

<text x="28" y="40" class="title">Top Languages</text>
"""

y = 75

for language, amount in languages.items():
    percent = amount / total * 100
    bar_width = percent * 4.2

    color = colors.get(language, "#8b949e")

    svg += f"""
<text x="28" y="{y}" class="label">{language}</text>

<rect
    x="130"
    y="{y - 13}"
    width="420"
    height="12"
    rx="6"
    fill="#21262d"
/>

<rect
    x="130"
    y="{y - 13}"
    width="{bar_width:.1f}"
    height="12"
    rx="6"
    fill="{color}"
/>

<text x="560" y="{y}" class="percent">{percent:.1f}%</text>
"""

    y += 42

svg += "</svg>"

os.makedirs("profile-summary-card-output/custom", exist_ok=True)

with open(
    "profile-summary-card-output/custom/top-languages.svg",
    "w",
    encoding="utf-8"
) as file:
    file.write(svg)
