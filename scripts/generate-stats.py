import os
from datetime import datetime, timezone
from pathlib import Path

import requests


USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = Path(
    "profile-summary-card-output/custom/stats.svg"
)

WIDTH = 340
HEIGHT = 200

BG = "#0d1117"
BORDER = "#30363d"
TITLE = "#58a6ff"
TEXT = "#c9d1d9"
GITHUB_LOGO = "#8b949e"

# Couleurs GitHub / Primer
STAR_COLOR = "#d29922"
COMMIT_COLOR = "#3fb950"
PR_COLOR = "#a371f7"
ISSUE_COLOR = "#f85149"
CONTRIB_COLOR = "#58a6ff"


if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required")


# ---------------------------------------------------------
# OCTICONS UTILISÉS PAR LE STATS ORIGINAL
# ---------------------------------------------------------

STAR_ICON = """
<path fill-rule="evenodd"
d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z"/>
"""

COMMIT_ICON = """
<path fill-rule="evenodd"
d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"/>
"""

PR_ICON = """
<path fill-rule="evenodd"
d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/>
"""

ISSUE_ICON = """
<path fill-rule="evenodd"
d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"/>
"""

REPOS_ICON = """
<path fill-rule="evenodd"
d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
"""

GITHUB_ICON = """
<path fill-rule="evenodd"
d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
"""


# ---------------------------------------------------------
# GITHUB GRAPHQL
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DONNÉES PRINCIPALES
# ---------------------------------------------------------

base_query = """
query($login: String!) {
  user(login: $login) {

    contributionsCollection {
      contributionYears
    }

    pullRequests(first: 1) {
      totalCount
    }

    issues(first: 1) {
      totalCount
    }

    repositoriesContributedTo(
      first: 1
      includeUserRepositories: true
      privacy: PUBLIC
      contributionTypes: [
        COMMIT
        ISSUE
        PULL_REQUEST
        REPOSITORY
      ]
    ) {
      totalCount
    }
  }
}
"""

base_data = graphql(
    base_query,
    {
        "login": USERNAME,
    },
)["user"]

contribution_years = (
    base_data["contributionsCollection"]["contributionYears"]
)

total_prs = base_data["pullRequests"]["totalCount"]
total_issues = base_data["issues"]["totalCount"]

total_contributed = (
    base_data["repositoriesContributedTo"]["totalCount"]
)


# ---------------------------------------------------------
# TOTAL STARS
# ---------------------------------------------------------

stars_query = """
query(
  $login: String!
  $after: String
) {
  user(login: $login) {
    repositories(
      first: 100
      after: $after
      privacy: PUBLIC
      isFork: false
      ownerAffiliations: OWNER
    ) {
      nodes {
        stargazerCount
      }

      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

total_stars = 0
after = None

while True:
    data = graphql(
        stars_query,
        {
            "login": USERNAME,
            "after": after,
        },
    )

    repositories = data["user"]["repositories"]

    for repo in repositories["nodes"]:
        total_stars += repo["stargazerCount"]

    page_info = repositories["pageInfo"]

    if not page_info["hasNextPage"]:
        break

    after = page_info["endCursor"]


# ---------------------------------------------------------
# TOTAL COMMITS — HISTORIQUE COMPLET
# ---------------------------------------------------------

commits_query = """
query(
  $login: String!
  $from: DateTime!
  $to: DateTime!
) {
  user(login: $login) {
    contributionsCollection(
      from: $from
      to: $to
    ) {
      totalCommitContributions
    }
  }
}
"""

total_commits = 0
now = datetime.now(timezone.utc)

for year in contribution_years:
    start = f"{year}-01-01T00:00:00Z"

    if year == now.year:
        end = now.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        end = f"{year}-12-31T23:59:59Z"

    data = graphql(
        commits_query,
        {
            "login": USERNAME,
            "from": start,
            "to": end,
        },
    )

    total_commits += (
        data["user"]
        ["contributionsCollection"]
        ["totalCommitContributions"]
    )


# ---------------------------------------------------------
# FORMAT DES NOMBRES
# ---------------------------------------------------------

def abbreviate_number(value):
    if value < 1000:
        return str(value)

    if value < 1_000_000:
        number = value / 1000
        suffix = "k"

    elif value < 1_000_000_000:
        number = value / 1_000_000
        suffix = "m"

    else:
        number = value / 1_000_000_000
        suffix = "b"

    rounded = round(number, 1)

    if rounded.is_integer():
        return f"{int(rounded)}{suffix}"

    return f"{rounded:.1f}{suffix}"


# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------

stats = [
    {
        "label": "Total Stars:",
        "value": abbreviate_number(total_stars),
        "color": STAR_COLOR,
        "icon": STAR_ICON,
    },
    {
        "label": "Total Commits:",
        "value": abbreviate_number(total_commits),
        "color": COMMIT_COLOR,
        "icon": COMMIT_ICON,
    },
    {
        "label": "Total PRs:",
        "value": abbreviate_number(total_prs),
        "color": PR_COLOR,
        "icon": PR_ICON,
    },
    {
        "label": "Total Issues:",
        "value": abbreviate_number(total_issues),
        "color": ISSUE_COLOR,
        "icon": ISSUE_ICON,
    },
    {
        "label": "Contributed to:",
        "value": abbreviate_number(total_contributed),
        "color": CONTRIB_COLOR,
        "icon": REPOS_ICON,
    },
]


# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

rows = []

LABEL_HEIGHT = 14
ROW_STEP = LABEL_HEIGHT * 1.8

for index, item in enumerate(stats):
    y = ROW_STEP * index

    rows.append(
        f'''
        <g transform="translate(0,{y:.1f})"
           fill="{item["color"]}">
            {item["icon"]}
        </g>

        <text
            x="21"
            y="{y + LABEL_HEIGHT:.1f}"
            fill="{TEXT}"
            font-size="14"
        >{item["label"]}</text>

        <text
            x="130"
            y="{y + LABEL_HEIGHT:.1f}"
            fill="{TEXT}"
            font-size="14"
        >{item["value"]}</text>
        '''
    )


svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
    <style>
        * {{
            font-family:
                'Segoe UI',
                Ubuntu,
                "Helvetica Neue",
                Sans-Serif;
        }}
    </style>

    <rect
        x="1"
        y="1"
        rx="5"
        ry="5"
        width="338"
        height="198"
        fill="{BG}"
        stroke="{BORDER}"
        stroke-width="1"
    />

    <text
        x="30"
        y="40"
        fill="{TITLE}"
        font-size="22"
    >Stats</text>

    <g transform="translate(0,40)">

        <g transform="translate(30,20)">
            {''.join(rows)}
        </g>

        <g transform="translate(220,20)">
            <g
                transform="scale(6)"
                fill="{GITHUB_LOGO}"
            >
                {GITHUB_ICON}
            </g>
        </g>

    </g>

</svg>
'''


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    svg,
    encoding="utf-8",
)

print("Stats")
print("-" * 32)
print(f"Total Stars:     {total_stars}")
print(f"Total Commits:   {total_commits}")
print(f"Total PRs:       {total_prs}")
print(f"Total Issues:    {total_issues}")
print(f"Contributed to:  {total_contributed}")
print("-" * 32)
print(f"Generated {OUTPUT}")
