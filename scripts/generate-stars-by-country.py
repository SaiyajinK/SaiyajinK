import json
import math
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from svgpathtools import parse_path


USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/stars-by-country.svg"
CACHE_FILE = "profile-summary-card-output/custom/stars-country-cache.json"

WIDTH = 650
HEIGHT = 230

WORLD_MAP_URL = (
    "https://simplemaps.com/static/demos/"
    "resources/svg-library/svgs/world.svg"
)

FLAG_URL = (
    "https://raw.githubusercontent.com/"
    "lipis/flag-icons/main/flags/4x3/{code}.svg"
)

BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

TITLE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#9da7b3"

MAP_FILL = "#152233"
MAP_STROKE = "#29405c"

BAR_BG = "#182537"
BAR_FILL = "#4b97ff"

POINT = "#6c79ff"
POINT_CORE = "#d0d8ff"

COUNTRY_NAME_OVERRIDES = {
    "US": "United States",
    "GB": "United Kingdom",
    "KR": "South Korea",
    "RU": "Russia",
    "DE": "Germany",
    "FR": "France",
    "CA": "Canada",
    "AU": "Australia",
    "IN": "India",
    "CN": "China",
    "JP": "Japan",
}

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


def download_text(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SaiyajinK-GitHub-Profile/1.0"},
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)


def geocode_location(location, cache):
    if location in cache:
        return cache[location]

    params = urllib.parse.urlencode(
        {
            "q": location,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        }
    )

    url = "https://nominatim.openstreetmap.org/search?" + params

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SaiyajinK-GitHub-Profile/1.0",
            "Accept-Language": "en",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            results = json.loads(response.read().decode("utf-8"))
    except Exception:
        cache[location] = None
        return None

    if not results:
        cache[location] = None
        return None

    item = results[0]
    address = item.get("address", {})

    result = {
        "country_code": (address.get("country_code") or "").upper(),
        "country_name": address.get("country") or "",
    }

    cache[location] = result
    time.sleep(1.05)
    return result


def number(value):
    if value >= 1000:
        result = f"{value / 1000:.1f}k"
        return result.replace(".0k", "k")
    return str(value)


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
        stargazerCount
      }
    }
  }
}
"""

stars_query = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    stargazers(first: 100, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        location
      }
    }
  }
}
"""

repos_data = graphql(repos_query, {"login": USERNAME})

repos = [
    repo
    for repo in repos_data["user"]["repositories"]["nodes"]
    if repo["stargazerCount"] > 0
]

raw_locations = Counter()

for repo in repos:
    repo_name = repo["name"]
    after = None

    print(f"Reading stars from {repo_name}...")

    while True:
        data = graphql(
            stars_query,
            {
                "owner": USERNAME,
                "name": repo_name,
                "after": after,
            },
        )

        stars = data["repository"]["stargazers"]

        for user in stars["nodes"]:
            location = (user.get("location") or "").strip()
            if location:
                raw_locations[location] += 1

        page = stars["pageInfo"]
        if not page["hasNextPage"]:
            break

        after = page["endCursor"]


cache = load_cache()

country_counts = Counter()
country_names = {}

for index, (location, count) in enumerate(raw_locations.most_common(), start=1):
    print(f"Geocoding {index}/{len(raw_locations)}: {location}")

    geo = geocode_location(location, cache)
    if not geo:
        continue

    code = geo["country_code"]
    if len(code) != 2:
        continue

    country_counts[code] += count
    country_names[code] = COUNTRY_NAME_OVERRIDES.get(
        code, geo["country_name"] or code
    )

save_cache(cache)

top_countries = country_counts.most_common(5)

resolved_total = sum(country_counts.values())
top_total = sum(count for _, count in top_countries)
other_count = max(resolved_total - top_total, 0)
display_total = max(resolved_total, 1)
max_count = max([count for _, count in top_countries] or [1])

print("Downloading world map template...")

world_svg_text = download_text(WORLD_MAP_URL)

ET.register_namespace("", "http://www.w3.org/2000/svg")
world_root = ET.fromstring(world_svg_text)

viewbox = world_root.get("viewBox", "0 0 1000 507")
vb = [float(value) for value in viewbox.split()]
VB_W = vb[2]
VB_H = vb[3]

country_boxes = {}


def add_bbox(code, bbox):
    xmin, xmax, ymin, ymax = bbox

    if code not in country_boxes:
        country_boxes[code] = [xmin, xmax, ymin, ymax]
        return

    old = country_boxes[code]
    country_boxes[code] = [
        min(old[0], xmin),
        max(old[1], xmax),
        min(old[2], ymin),
        max(old[3], ymax),
    ]


for element in world_root.iter():
    tag = element.tag.split("}")[-1]

    if tag in ("path", "polygon", "polyline"):
        element.set("fill", MAP_FILL)
        element.set("stroke", MAP_STROKE)
        element.set("stroke-width", "0.7")
        element.attrib.pop("style", None)

    if tag != "path":
        continue

    d = element.get("d")
    code = (element.get("id") or "").upper()

    if not d or len(code) != 2:
        continue

    try:
        bbox = parse_path(d).bbox()
        add_bbox(code, bbox)
    except Exception:
        pass


world_inner = "".join(
    ET.tostring(child, encoding="unicode")
    for child in list(world_root)
)

bubble_svg = []

for code, count in country_counts.items():
    if code not in country_boxes:
        continue

    xmin, xmax, ymin, ymax = country_boxes[code]
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2

    ratio = count / max_count
    radius = 4.0 + math.sqrt(ratio) * 11.0

    bubble_svg.append(
        f'''
        <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 2.5:.2f}" fill="{POINT}" opacity="0.08"/>
        <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 1.6:.2f}" fill="{POINT}" opacity="0.16"/>
        <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="{POINT}" opacity="0.82"/>
        <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{max(1.8, radius * 0.20):.2f}" fill="{POINT_CORE}"/>
        '''
    )

flag_cache = {}


def flag_svg(code, x, y):
    code_lower = code.lower()

    if code_lower not in flag_cache:
        try:
            source = download_text(FLAG_URL.format(code=code_lower))
            root = ET.fromstring(source)
            flag_viewbox = root.get("viewBox", "0 0 640 480")
            inner = "".join(
                ET.tostring(child, encoding="unicode")
                for child in list(root)
            )
            flag_cache[code_lower] = (flag_viewbox, inner)
        except Exception:
            flag_cache[code_lower] = None

    result = flag_cache[code_lower]

    if not result:
        return (
            f'<text x="{x}" y="{y + 10}" fill="{TEXT}" font-size="9" '
            f'font-family="Segoe UI, Arial, sans-serif">{code.upper()}</text>'
        )

    flag_viewbox, inner = result

    return f'''
    <svg x="{x}" y="{y}" width="16" height="12" viewBox="{flag_viewbox}" preserveAspectRatio="xMidYMid slice">
        {inner}
    </svg>
    '''


rows = []

ROW_START_Y = 82
ROW_GAP = 24

RANK_X = 406
FLAG_X = 420
NAME_X = 442
VALUE_X = 553
BAR_X = 560
BAR_W = 50
PCT_X = 632

for index, (code, count) in enumerate(top_countries, start=1):
    y = ROW_START_Y + (index - 1) * ROW_GAP
    percent = count / display_total * 100
    progress = count / max_count * BAR_W

    country_name = country_names.get(code, code)

    rows.append(
        f'''
        <text x="{RANK_X}" y="{y}" fill="{TEXT}" font-size="10" font-family="Segoe UI, Arial, sans-serif">{index}</text>
        {flag_svg(code, FLAG_X, y - 10)}
        <text x="{NAME_X}" y="{y}" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">{country_name}</text>
        <text x="{VALUE_X}" y="{y}" text-anchor="end" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">{number(count)}</text>
        <rect x="{BAR_X}" y="{y - 7}" width="{BAR_W}" height="7" rx="3.5" fill="{BAR_BG}"/>
        <rect x="{BAR_X}" y="{y - 7}" width="{progress:.2f}" height="7" rx="3.5" fill="{BAR_FILL}"/>
        <text x="{PCT_X}" y="{y}" text-anchor="end" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">{percent:.0f}%</text>
        '''
    )

other_percent = other_count / display_total * 100
other_progress = min(other_count / max_count * BAR_W, BAR_W)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="cardBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#101722"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="7" fill="url(#cardBg)" stroke="{BORDER}"/>

  <path d="M16 12 L19.6 21.8 L30 22.1 L21.8 28.5 L24.8 38 L16 32 L7.2 38 L10.2 28.5 L2 22.1 L12.4 21.8 Z"
        fill="none" stroke="{TITLE}" stroke-width="1.7" stroke-linejoin="round"/>

  <text x="36" y="31" fill="{TITLE}" font-size="16.5" font-weight="600" font-family="Segoe UI, Arial, sans-serif">Stars by country</text>

  <text x="610" y="29" text-anchor="end" fill="{MUTED}" font-size="8.6" font-family="Segoe UI, Arial, sans-serif">Geographic distribution of repository stars</text>

  <circle cx="628" cy="24" r="7" fill="none" stroke="{MUTED}" stroke-width="1"/>
  <text x="628" y="27" text-anchor="middle" fill="{MUTED}" font-size="8" font-family="Segoe UI, Arial, sans-serif">i</text>

  <rect x="10" y="42" width="630" height="176" rx="6" fill="none" stroke="{INNER_BORDER}"/>

  <svg
      x="20"
      y="58"
      width="350"
      height="112"
      viewBox="{viewbox}"
      preserveAspectRatio="xMidYMid meet">
      {world_inner}
      {''.join(bubble_svg)}
  </svg>

  <rect x="24" y="171" width="96" height="30" rx="5" fill="#101722" stroke="{INNER_BORDER}"/>
  <text x="32" y="182" fill="{MUTED}" font-size="6.4" font-family="Segoe UI, Arial, sans-serif">Number of stars</text>
  <circle cx="35" cy="192" r="1.7" fill="{POINT}"/>
  <circle cx="53" cy="192" r="2.6" fill="{POINT}"/>
  <circle cx="74" cy="192" r="4.0" fill="{POINT}"/>
  <circle cx="99" cy="192" r="6.3" fill="{POINT}"/>
  <text x="35" y="200" text-anchor="middle" fill="{MUTED}" font-size="5.8" font-family="Segoe UI, Arial, sans-serif">1</text>
  <text x="53" y="200" text-anchor="middle" fill="{MUTED}" font-size="5.8" font-family="Segoe UI, Arial, sans-serif">10</text>
  <text x="74" y="200" text-anchor="middle" fill="{MUTED}" font-size="5.8" font-family="Segoe UI, Arial, sans-serif">50</text>
  <text x="99" y="200" text-anchor="middle" fill="{MUTED}" font-size="5.8" font-family="Segoe UI, Arial, sans-serif">100+</text>

  <line x1="392" y1="56" x2="392" y2="206" stroke="{INNER_BORDER}"/>

  {''.join(rows)}

  <line x1="406" y1="189" x2="632" y2="189" stroke="{INNER_BORDER}"/>

  <circle cx="422" cy="204" r="6.5" fill="none" stroke="{MUTED}" stroke-width="1"/>
  <path d="M416 204 H428 M422 198 C419 200 419 208 422 210 M422 198 C425 200 425 208 422 210"
        fill="none" stroke="{MUTED}" stroke-width="0.75"/>

  <text x="{NAME_X}" y="207" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">Other countries</text>
  <text x="{VALUE_X}" y="207" text-anchor="end" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">{number(other_count)}</text>
  <rect x="{BAR_X}" y="200" width="{BAR_W}" height="7" rx="3.5" fill="{BAR_BG}"/>
  <rect x="{BAR_X}" y="200" width="{other_progress:.2f}" height="7" rx="3.5" fill="{BAR_FILL}"/>
  <text x="{PCT_X}" y="207" text-anchor="end" fill="{TEXT}" font-size="9.8" font-family="Segoe UI, Arial, sans-serif">{other_percent:.0f}%</text>
</svg>
'''

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated {OUTPUT}")
