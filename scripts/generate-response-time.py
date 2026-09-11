import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/response-time.svg"

WIDTH = 860
HEIGHT = 220

BG = "#0d1117"
INNER_BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

BLUE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#9da7b3"

GREEN = "#3ddc97"
MID_BLUE = "#438cff"
PINK = "#ff4d94"

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required")


def graphql(query, variables=None):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(
            {
                "query": query,
                "variables": variables or {},
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": USERNAME,
        },
    )

    with urllib.request.urlopen(request) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]


repos_query = """
query($login: String!) {
  user(login: $login) {
    repositories(
      first: 100
      ownerAffiliations: OWNER
      isFork: false
      privacy: PUBLIC
    ) {
      nodes {
        name
      }
    }
  }
}
"""

repo_data = graphql(
    repos_query,
    {"login": USERNAME},
)

repos = [
    repo["name"]
    for repo in repo_data["user"]["repositories"]["nodes"]
]


repo_query = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {

    issues(
      first: 100
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      nodes {
        createdAt

        author {
          login
        }

        comments(first: 100) {
          nodes {
            createdAt

            author {
              login
            }
          }
        }
      }
    }

    discussions(
      first: 100
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      nodes {
        createdAt

        author {
          login
        }

        comments(first: 100) {
          nodes {
            createdAt

            author {
              login
            }
          }
        }
      }
    }
  }
}
"""


def parse_date(value):
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


response_hours = []


def process_nodes(nodes):
    for item in nodes:
        author = item.get("author")

        if not author:
            continue

        if author.get("login", "").lower() == USERNAME.lower():
            continue

        created = parse_date(
            item["createdAt"]
        )

        first_reply = None

        for comment in item["comments"]["nodes"]:
            comment_author = comment.get("author")

            if not comment_author:
                continue

            if (
                comment_author.get("login", "").lower()
                == USERNAME.lower()
            ):
                reply_date = parse_date(
                    comment["createdAt"]
                )

                if (
                    first_reply is None
                    or reply_date < first_reply
                ):
                    first_reply = reply_date

        if first_reply is None:
            continue

        hours = (
            first_reply - created
        ).total_seconds() / 3600

        if hours >= 0:
            response_hours.append(hours)


for repo in repos:
    print(f"Analyse de {repo}...")

    try:
        data = graphql(
            repo_query,
            {
                "owner": USERNAME,
                "name": repo,
            },
        )
    except Exception as error:
        print(
            f"Impossible d'analyser {repo}: {error}"
        )
        continue

    repository = data.get("repository")

    if not repository:
        continue

    process_nodes(
        repository["issues"]["nodes"]
    )

    process_nodes(
        repository["discussions"]["nodes"]
    )


if response_hours:
    average_hours = (
        sum(response_hours)
        / len(response_hours)
    )
else:
    average_hours = 0


under_24 = sum(
    1
    for value in response_hours
    if value < 24
)

between_24_72 = sum(
    1
    for value in response_hours
    if 24 <= value <= 72
)

over_72 = sum(
    1
    for value in response_hours
    if value > 72
)

total = max(
    len(response_hours),
    1,
)

pct_fast = under_24 / total * 100
pct_normal = between_24_72 / total * 100
pct_slow = over_72 / total * 100


if average_hours < 24:
    average_text = (
        f"{average_hours:.1f} h"
    )
else:
    average_text = (
        f"{average_hours / 24:.1f} jours"
    )


bar_x = 360
bar_y = 96
bar_w = 450
bar_h = 12

w_fast = bar_w * pct_fast / 100
w_normal = bar_w * pct_normal / 100
w_slow = bar_w * pct_slow / 100


svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>

    <rect
        x="0.5"
        y="0.5"
        width="{WIDTH - 1}"
        height="{HEIGHT - 1}"
        rx="8"
        fill="{BG}"
        stroke="{BORDER}"
    />

    <text
        x="28"
        y="36"
        fill="{BLUE}"
        font-size="22"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >Temps de réponse</text>

    <text
        x="{WIDTH - 28}"
        y="35"
        text-anchor="end"
        fill="{MUTED}"
        font-size="11"
        font-family="Segoe UI, Arial, sans-serif"
    >Délai moyen pour répondre aux issues et discussions</text>

    <rect
        x="20"
        y="54"
        width="{WIDTH - 40}"
        height="145"
        rx="7"
        fill="{INNER_BG}"
        stroke="{INNER_BORDER}"
    />

    <circle
        cx="92"
        cy="126"
        r="43"
        fill="none"
        stroke="#428cff"
        stroke-width="6"
    />

    <circle
        cx="92"
        cy="126"
        r="29"
        fill="none"
        stroke="#428cff"
        stroke-width="3"
        opacity="0.45"
    />

    <line
        x1="92"
        y1="126"
        x2="92"
        y2="105"
        stroke="#428cff"
        stroke-width="5"
        stroke-linecap="round"
    />

    <line
        x1="92"
        y1="126"
        x2="108"
        y2="137"
        stroke="#428cff"
        stroke-width="5"
        stroke-linecap="round"
    />

    <text
        x="152"
        y="92"
        fill="{MUTED}"
        font-size="13"
        font-family="Segoe UI, Arial, sans-serif"
    >Temps de réponse moyen</text>

    <text
        x="152"
        y="137"
        fill="{TEXT}"
        font-size="37"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >{average_text}</text>

    <text
        x="152"
        y="165"
        fill="{MUTED}"
        font-size="12"
        font-family="Segoe UI, Arial, sans-serif"
    >Basé sur {len(response_hours)} réponses publiques</text>

    <line
        x1="330"
        y1="70"
        x2="330"
        y2="182"
        stroke="{INNER_BORDER}"
    />

    <rect
        x="{bar_x}"
        y="{bar_y}"
        width="{bar_w}"
        height="{bar_h}"
        rx="6"
        fill="#182435"
    />

    <rect
        x="{bar_x}"
        y="{bar_y}"
        width="{w_fast:.2f}"
        height="{bar_h}"
        rx="6"
        fill="{GREEN}"
    />

    <rect
        x="{bar_x + w_fast:.2f}"
        y="{bar_y}"
        width="{w_normal:.2f}"
        height="{bar_h}"
        fill="{MID_BLUE}"
    />

    <rect
        x="{bar_x + w_fast + w_normal:.2f}"
        y="{bar_y}"
        width="{w_slow:.2f}"
        height="{bar_h}"
        rx="6"
        fill="{PINK}"
    />

    <circle
        cx="382"
        cy="134"
        r="6"
        fill="{GREEN}"
    />

    <text
        x="400"
        y="139"
        fill="{TEXT}"
        font-size="13"
        font-family="Segoe UI, Arial, sans-serif"
    >Moins d’un jour</text>

    <text
        x="400"
        y="166"
        fill="{TEXT}"
        font-size="18"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >{pct_fast:.0f}%</text>

    <circle
        cx="555"
        cy="134"
        r="6"
        fill="{MID_BLUE}"
    />

    <text
        x="573"
        y="139"
        fill="{TEXT}"
        font-size="13"
        font-family="Segoe UI, Arial, sans-serif"
    >1 à 3 jours</text>

    <text
        x="573"
        y="166"
        fill="{TEXT}"
        font-size="18"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >{pct_normal:.0f}%</text>

    <circle
        cx="704"
        cy="134"
        r="6"
        fill="{PINK}"
    />

    <text
        x="722"
        y="139"
        fill="{TEXT}"
        font-size="13"
        font-family="Segoe UI, Arial, sans-serif"
    >Plus de 3 jours</text>

    <text
        x="722"
        y="166"
        fill="{TEXT}"
        font-size="18"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >{pct_slow:.0f}%</text>

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

print(
    f"Generated {OUTPUT}"
)
