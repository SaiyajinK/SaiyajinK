import json
import os
import urllib.request
from datetime import datetime

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/response-time.svg"

WIDTH = 210
HEIGHT = 250

BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

TITLE = "#008cff"
TEXT = "#ffffff"
MUTED = "#c9d1d9"
SUBTLE = "#9da7b3"

GREEN = "#28e07c"
GREEN_BG = "#173226"
GREEN_ICON = "#1de06f"

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

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]


def parse_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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

repo_query = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(
      first: 100
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      nodes {
        createdAt
        author { login }
        comments(first: 100) {
          nodes {
            createdAt
            author { login }
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
        author { login }
        comments(first: 100) {
          nodes {
            createdAt
            author { login }
          }
        }
      }
    }
  }
}
"""

repos_data = graphql(repos_query, {"login": USERNAME})
repos = [repo["name"] for repo in repos_data["user"]["repositories"]["nodes"]]

response_hours = []


def process_nodes(nodes):
    for item in nodes:
        author = item.get("author")
        if not author:
            continue

        author_login = (author.get("login") or "").lower()
        if author_login == USERNAME.lower():
            continue

        created = parse_date(item["createdAt"])
        first_reply = None

        for comment in item["comments"]["nodes"]:
            comment_author = comment.get("author")
            if not comment_author:
                continue

            comment_login = (comment_author.get("login") or "").lower()
            if comment_login != USERNAME.lower():
                continue

            reply_date = parse_date(comment["createdAt"])
            if first_reply is None or reply_date < first_reply:
                first_reply = reply_date

        if first_reply is None:
            continue

        delay_hours = (first_reply - created).total_seconds() / 3600.0
        if delay_hours >= 0:
            response_hours.append(delay_hours)


for repo in repos:
    try:
        data = graphql(repo_query, {"owner": USERNAME, "name": repo})
        repository = data.get("repository")
        if not repository:
            continue

        process_nodes(repository["issues"]["nodes"])
        process_nodes(repository["discussions"]["nodes"])

    except Exception as error:
        print(f"Skipping {repo}: {error}")


count_total = len(response_hours)

if count_total == 0:
    average_hours = 0
    pct_under_24 = 0
    pct_24_72 = 0
    pct_over_72 = 0
else:
    average_hours = sum(response_hours) / count_total
    under_24 = sum(1 for h in response_hours if h < 24)
    between_24_72 = sum(1 for h in response_hours if 24 <= h <= 72)
    over_72 = sum(1 for h in response_hours if h > 72)

    pct_under_24 = round(under_24 / count_total * 100)
    pct_24_72 = round(between_24_72 / count_total * 100)
    pct_over_72 = round(over_72 / count_total * 100)

avg_days = average_hours / 24 if average_hours else 0
avg_text = f"{avg_days:.1f} days"

progress_pct = max(8, min(100, pct_under_24))
progress_width = 128 * progress_pct / 100.0

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="cardBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#101722"/>
    </linearGradient>

    <linearGradient id="greenBar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#18d7a0"/>
      <stop offset="100%" stop-color="#28e07c"/>
    </linearGradient>

    <filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="url(#cardBg)" stroke="{BORDER}"/>
  <rect x="8" y="8" width="{WIDTH - 16}" height="{HEIGHT - 16}" rx="8" fill="none" stroke="{INNER_BORDER}"/>

  <text x="16" y="30" fill="{TEXT}" font-size="18" font-weight="600" font-family="Segoe UI, Arial, sans-serif">Response time</text>
  <text x="16" y="50" fill="{MUTED}" font-size="10.5" font-family="Segoe UI, Arial, sans-serif">Average delay to reply to issues.</text>

  <circle cx="36" cy="95" r="20" fill="{GREEN_BG}" filter="url(#softGlow)"/>
  <path d="M38 77 L28 97 H37 L33 115 L47 92 H38 Z" fill="{GREEN_ICON}"/>

  <text x="60" y="99" fill="{TEXT}" font-size="18" font-weight="700" font-family="Segoe UI, Arial, sans-serif">{avg_text}</text>

  <rect x="16" y="116" width="128" height="9" rx="4.5" fill="{GREEN_BG}"/>
  <rect x="16" y="116" width="{progress_width:.1f}" height="9" rx="4.5" fill="url(#greenBar)"/>

  <text x="16" y="145" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">&lt; 1 day</text>
  <text x="194" y="145" text-anchor="end" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">{pct_under_24}%</text>

  <text x="16" y="166" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">1-3 days</text>
  <text x="194" y="166" text-anchor="end" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">{pct_24_72}%</text>

  <text x="16" y="187" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">&gt; 3 days</text>
  <text x="194" y="187" text-anchor="end" fill="{TEXT}" font-size="11" font-family="Segoe UI, Arial, sans-serif">{pct_over_72}%</text>

</svg>
'''

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated {OUTPUT}")
