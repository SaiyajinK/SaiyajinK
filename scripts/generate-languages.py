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


# Garde uniquement les 4 langages les plus utilisés
languages = dict(
    sorted(
        languages.items(),
        key=lambda x: x[1],
        reverse=True
    )[:4]
)

total = sum(languages.values())

colors = {
    "CSS": "#663399",
    "JavaScript": "#f1e05a",
    "PowerShell": "#012456",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CMake": "#DA3434"
}

width = 600
height = 58 + len(languages) * 30

svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
>
<style>

.title {{
    font: 20px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    fill: #2f81f7;
}}

.label {{
    font: 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    fill: #8b949e;
}}

.percent {{
    font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
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
    x="28"
    y="34"
    class="title"
>
Top Languages
</text>
"""

y = 62

for language, amount in languages.items():

    percent = (amount / total * 100) if total else 0

    bar_max_width = 390
    bar_width = (percent / 100) * bar_max_width

    color = colors.get(language, "#8b949e")

    svg += f"""
<text
    x="28"
    y="{y}"
    class="label"
>
{language}
</text>

<rect
    x="125"
    y="{y - 9}"
    width="{bar_max_width}"
    height="8"
    rx="4"
    fill="#21262d"
/>

<rect
    x="125"
    y="{y - 9}"
    width="{bar_width:.1f}"
    height="8"
    rx="4"
    fill="{color}"
/>

<text
    x="530"
    y="{y}"
    class="percent"
>
{percent:.1f}%
</text>
"""

    y += 30

svg += """
</svg>
"""

output_dir = "profile-summary-card-output/custom"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(
    output_dir,
    "top-languages.svg"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:
    file.write(svg)

print(f"Generated: {output_file}")
