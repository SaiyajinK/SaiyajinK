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


# Langages que l'on veut TOUJOURS afficher
LANGUAGES = [
    "CSS",
    "C++",
    "JavaScript",
    "Python",
    "PowerShell"
]

colors = {
    "CSS": "#663399",
    "C++": "#f34b7d",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "PowerShell": "#012456"
}

# Calcul des vrais pourcentages
total = sum(languages_data.values())

languages = []

for language in LANGUAGES:
    amount = languages_data.get(language, 0)

    percent = (
        amount / total * 100
        if total > 0 else 0
    )

    languages.append(
        (language, percent)
    )


WIDTH = 500
HEIGHT = 105

BAR_X = 24
BAR_Y = 42
BAR_WIDTH = 452
BAR_HEIGHT = 12

SEGMENT_COUNT = 5
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
    font-weight: 500;
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
    width="{WIDTH - 1}"
    height="{HEIGHT - 1}"
    rx="6"
    fill="#0d1117"
    stroke="#30363d"
/>


<!-- TITRE -->

<text
    x="{WIDTH / 2}"
    y="25"
    text-anchor="middle"
    class="title"
>
Top Languages
</text>


<!-- BARRE -->

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


# 5 portions exactement égales
for index, (language, percent) in enumerate(languages):

    x = BAR_X + index * SEGMENT_WIDTH
    color = colors[language]

    svg += f"""
<rect
    x="{x:.2f}"
    y="{BAR_Y}"
    width="{SEGMENT_WIDTH + 0.5:.2f}"
    height="{BAR_HEIGHT}"
    fill="{color}"
/>
"""


svg += """
</g>
"""


# LÉGENDE
#
# Chaque élément possède exactement la même largeur que
# son segment et son contenu est centré dans cette zone.

LEGEND_Y = 78

for index, (language, percent) in enumerate(languages):

    center_x = (
        BAR_X
        + index * SEGMENT_WIDTH
        + SEGMENT_WIDTH / 2
    )

    color = colors[language]

    # Groupe entier centré sous le segment
    svg += f"""
<g transform="translate({center_x:.2f}, 0)">

    <circle
        cx="-27"
        cy="{LEGEND_Y - 3}"
        r="3"
        fill="{color}"
    />

    <text
        x="3"
        y="{LEGEND_Y}"
        text-anchor="middle"
        class="legend"
    >
        {language} {percent:.1f}%
    </text>

</g>
"""


svg += """
</svg>
"""


output_dir = "profile-summary-card-output/custom"

os.makedirs(
    output_dir,
    exist_ok=True
)

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


print(
    f"Generated: {output_file}"
)
