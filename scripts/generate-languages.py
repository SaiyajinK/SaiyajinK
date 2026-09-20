import os
import requests

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/languages-5-equal-v2.svg"

WIDTH = 474
HEIGHT = 218

BG = "#0D1117"
BORDER = "#30363D"
TITLE = "#00A4EF"
TEXT = "#F0F6FC"
MUTED = "#9DA7B3"

LANGUAGES = [
    ("CSS", "#C653F4"),
    ("C++", "#FF4D8A"),
    ("JavaScript", "#F5DF4D"),
    ("Python", "#4AA7F5"),
    ("PowerShell", "#0878CC"),
    ("Lua", "#2EA44F"),
    ("Shell", "#FF812D"),
    ("TypeScript", "#16C6C8"),
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
        json={
            "query": query,
            "variables": variables or {},
        },
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
      orderBy: {
        field: PUSHED_AT
        direction: DESC
      }
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }

      nodes {
        languages(
          first: 100
          orderBy: {
            field: SIZE
            direction: DESC
          }
        ) {
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
    data = graphql(
        query,
        {
            "login": USERNAME,
            "after": after,
        },
    )

    repositories = (
        data["user"]
        ["repositories"]
    )

    for repo in repositories["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size = edge["size"]

            language_sizes[name] = (
                language_sizes.get(name, 0)
                + size
            )

    page_info = repositories["pageInfo"]

    if not page_info["hasNextPage"]:
        break

    after = page_info["endCursor"]


# On conserve exactement les 8 langages demandés.
# Un langage absent reste affiché à 0.00 %.

items = []

for name, color in LANGUAGES:
    items.append(
        {
            "name": name,
            "color": color,
            "size": language_sizes.get(name, 0),
        }
    )


# Les pourcentages sont calculés uniquement
# sur les 8 langages affichés.

total = sum(
    item["size"]
    for item in items
)

if total <= 0:
    total = 1


for item in items:
    item["percent"] = (
        item["size"]
        / total
        * 100
    )


# ---------------------------------------------------------
# BARRE SUPÉRIEURE
# ---------------------------------------------------------
#
# On conserve exactement la disposition du preview :
#
# CSS        78 px
# C++        78 px
# JavaScript 78 px
# Python     78 px
# PowerShell 31 px
# Lua        16 px
# Shell      16 px
# TypeScript 15 px
#
# Total = 390 px
#
# La barre reste donc visuellement identique au mockup,
# tandis que les pourcentages affichés restent dynamiques.

bar_segments = [
    (41, 78),
    (119, 78),
    (197, 78),
    (275, 78),
    (353, 31),
    (384, 16),
    (400, 16),
    (416, 15),
]


bar_svg = []

for item, (x, width) in zip(
    items,
    bar_segments,
):
    bar_svg.append(
        f'''
        <rect
            x="{x}"
            y="92"
            width="{width}"
            height="8"
            fill="{item["color"]}"
        />
        '''
    )


# ---------------------------------------------------------
# GRILLE 4 × 2
# ---------------------------------------------------------

positions = [
    # Ligne 1
    (57, 67, 123, 127, 143),
    (157, 167, 123, 127, 143),
    (257, 267, 123, 127, 143),
    (367, 377, 123, 127, 143),

    # Ligne 2
    (57, 67, 161, 165, 181),
    (157, 167, 161, 165, 181),
    (257, 267, 161, 165, 181),
    (367, 377, 161, 165, 181),
]


languages_svg = []


for item, position in zip(
    items,
    positions,
):
    (
        circle_x,
        text_x,
        circle_y,
        name_y,
        percent_y,
    ) = position

    languages_svg.append(
        f'''
        <circle
            cx="{circle_x}"
            cy="{circle_y}"
            r="3"
            fill="{item["color"]}"
        />

        <text
            x="{text_x}"
            y="{name_y}"
            fill="{TEXT}"
            font-family="Segoe UI, Arial, sans-serif"
            font-size="10"
            font-weight="500"
        >{item["name"]}</text>

        <text
            x="{text_x}"
            y="{percent_y}"
            fill="{MUTED}"
            font-family="Segoe UI, Arial, sans-serif"
            font-size="9"
        >{item["percent"]:.2f}%</text>
        '''
    )


svg = f'''<svg
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    xmlns="http://www.w3.org/2000/svg"
>

    <defs>
        <clipPath id="barClip">
            <rect
                x="41"
                y="92"
                width="390"
                height="8"
                rx="4"
            />
        </clipPath>
    </defs>

    <rect
        x="15"
        y="25"
        width="444"
        height="176"
        rx="7"
        fill="{BG}"
        stroke="{BORDER}"
        stroke-width="1"
    />

    <text
        x="237"
        y="71"
        text-anchor="middle"
        fill="{TITLE}"
        font-family="Segoe UI, Arial, sans-serif"
        font-size="16"
        font-weight="600"
    >Top Languages</text>

    <g clip-path="url(#barClip)">
        {''.join(bar_svg)}
    </g>

    {''.join(languages_svg)}

</svg>
'''


os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True,
)


with open(
    OUTPUT,
    "w",
    encoding="utf-8",
) as file:
    file.write(svg)


print("Top Languages")
print("-" * 40)

for item in items:
    print(
        f'{item["name"]:<12} '
        f'{item["percent"]:>7.2f}%'
    )

print("-" * 40)
print(f"Generated {OUTPUT}")
