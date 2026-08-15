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

    data = requests.get(repo["languages_url"], headers=headers).json()

    for language, amount in data.items():
        languages[language] = languages.get(language, 0) + amount

# 5 langages maximum
languages = sorted(
    languages.items(),
    key=lambda x: x[1],
    reverse=True
)[:5]

total = sum(amount for _, amount in languages)

colors = {
    "CSS": "#663399",
    "JavaScript": "#f1e05a",
    "PowerShell": "#012456",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "HTML": "#e34c26"
}

width = 500
height = 175

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="{width}" height="{height}"
viewBox="0 0 {width} {height}">

<style>
.title {{
    font: 20px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    fill: #2f81f7;
}}
.label {{
    font: 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    fill: #8b949e;
}}
.percent {{
    font: 11px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    fill: #8b949e;
}}
</style>

<rect x="0.5" y="0.5"
width="{width - 1}" height="{height - 1}"
rx="6"
fill="#0d1117"
stroke="#30363d"/>

<text x="24" y="30" class="title">Top Languages</text>
"""

y = 57
bar_x = 115
bar_max = 300

for language, amount in languages:
    percent = (amount / total * 100) if total else 0
    bar_width = max((percent / 100) * bar_max, 2)
    color = colors.get(language, "#8b949e")

    svg += f"""
<text x="24" y="{y + 4}" class="label">{language}</text>

<rect
    x="{bar_x}"
    y="{y - 7}"
    width="{bar_max}"
    height="8"
    rx="4"
    fill="#21262d"
/>

<rect
    x="{bar_x}"
    y="{y - 7}"
    width="{bar_width:.1f}"
    height="8"
    rx="4"
    fill="{color}"
/>

<text
    x="425"
    y="{y + 4}"
    class="percent"
>{percent:.1f}%</text>
"""
    y += 23

svg += "</svg>"

output = "profile-summary-card-output/custom"
os.makedirs(output, exist_ok=True)

with open(
    f"{output}/top-languages.svg",
    "w",
    encoding="utf-8"
) as f:
    f.write(svg)

print("top-languages.svg generated")
