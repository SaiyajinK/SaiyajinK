import json
import math
import os
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/stars-by-country.svg"
CACHE_FILE = "profile-summary-card-output/custom/stars-country-cache.json"

WIDTH = 980
HEIGHT = 300

BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

TITLE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#9da7b3"

MAP_FILL = "#162232"
MAP_STROKE = "#29405c"

BAR_BG = "#182537"
BAR_FILL = "#4b97ff"

GLOW = "#6d78ff"
CORE = "#b7c5ff"

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


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def format_number(value):
    if value >= 1000:
        text = f"{value / 1000:.1f}k"
        return text.replace(".0k", "k")
    return str(value)


def flag_emoji(country_code):
    if not country_code or len(country_code) != 2:
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())


def project(lon, lat, map_x, map_y, map_w, map_h):
    x = map_x + ((lon + 180.0) / 360.0) * map_w
    y = map_y + ((90.0 - lat) / 180.0) * map_h
    return x, y


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
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
    }

    cache[location] = result
    time.sleep(1.05)
    return result


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

stargazers_query = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    stargazers(first: 100, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        login
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
    name = repo["name"]
    after = None

    print(f"Reading stargazers from {name}...")

    while True:
        data = graphql(
            stargazers_query,
            {
                "owner": USERNAME,
                "name": name,
                "after": after,
            },
        )

        stargazers = data["repository"]["stargazers"]

        for user in stargazers["nodes"]:
            location = (user.get("location") or "").strip()
            if location:
                raw_locations[location] += 1

        page_info = stargazers["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        after = page_info["endCursor"]


cache = load_cache()

country_counts = Counter()
country_names = {}
map_points = defaultdict(lambda: {"count": 0, "lat": 0.0, "lon": 0.0})

resolved_total = 0

for index, (location, count) in enumerate(raw_locations.most_common(), start=1):
    print(f"Geocoding {index}/{len(raw_locations)}: {location}")
    geo = geocode_location(location, cache)

    if not geo:
        continue

    country_code = geo["country_code"]
    country_name = geo["country_name"]

    if not country_code:
        continue

    country_counts[country_code] += count
    country_names[country_code] = country_name
    resolved_total += count

    key = (round(geo["lat"], 1), round(geo["lon"], 1))
    map_points[key]["count"] += count
    map_points[key]["lat"] = geo["lat"]
    map_points[key]["lon"] = geo["lon"]

save_cache(cache)

top_countries = country_counts.most_common(5)
top_sum = sum(count for _, count in top_countries)
other_count = max(resolved_total - top_sum, 0)

display_total = max(resolved_total, 1)
max_count = max([count for _, count in top_countries] or [1])

MAP_X = 38
MAP_Y = 84
MAP_W = 492
MAP_H = 170

world_paths = []
WORLD_URL = "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"

try:
    request = urllib.request.Request(
        WORLD_URL,
        headers={"User-Agent": "SaiyajinK-GitHub-Profile/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        world = json.loads(response.read().decode("utf-8"))

    for feature in world["features"]:
        geometry = feature.get("geometry")
        if not geometry:
            continue

        geom_type = geometry["type"]
        coordinates = geometry["coordinates"]

        if geom_type == "Polygon":
            polygons = [coordinates]
        elif geom_type == "MultiPolygon":
            polygons = coordinates
        else:
            continue

        for polygon in polygons:
            for ring in polygon:
                if not ring:
                    continue

                commands = []
                for i, (lon, lat) in enumerate(ring):
                    x, y = project(lon, lat, MAP_X, MAP_Y, MAP_W, MAP_H)
                    commands.append(
                        f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}'
                    )
                commands.append("Z")

                world_paths.append(
                    f'<path d="{" ".join(commands)}" fill="{MAP_FILL}" stroke="{MAP_STROKE}" stroke-width="0.45"/>'
                )
except Exception as error:
    print(f"World map download failed: {error}")


point_svg = []
for _, point in sorted(
    map_points.items(),
    key=lambda item: item[1]["count"],
    reverse=True,
)[:40]:
    x, y = project(point["lon"], point["lat"], MAP_X, MAP_Y, MAP_W, MAP_H)
    count = point["count"]

    radius = min(3.0 + math.sqrt(count) * 1.1, 12.0)
    outer = radius * 2.4

    point_svg.append(
        f'''
        <circle cx="{x:.1f}" cy="{y:.1f}" r="{outer:.1f}" fill="{GLOW}" opacity="0.10"/>
        <circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{GLOW}" opacity="0.88"/>
        <circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{CORE}"/>
        '''
    )


rows_svg = []
list_x_rank = 580
list_x_flag = 612
list_x_name = 646
list_x_value = 820
list_x_bar = 835
list_x_pct = 950
row_start_y = 108
row_gap = 28
bar_width = 92

for i, (code, count) in enumerate(top_countries, start=1):
    y = row_start_y + (i - 1) * row_gap
    percent = count / display_total * 100
    progress = (count / max_count) * bar_width
    name = country_names.get(code, code)

    rows_svg.append(
        f'''
        <text x="{list_x_rank}" y="{y}" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{i}</text>
        <text x="{list_x_flag}" y="{y}" fill="{TEXT}" font-size="16" font-family="Segoe UI Emoji, Segoe UI, Arial">{flag_emoji(code)}</text>
        <text x="{list_x_name}" y="{y}" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{name}</text>
        <text x="{list_x_value}" y="{y}" text-anchor="end" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{format_number(count)}</text>
        <rect x="{list_x_bar}" y="{y - 10}" width="{bar_width}" height="8" rx="4" fill="{BAR_BG}"/>
        <rect x="{list_x_bar}" y="{y - 10}" width="{progress:.1f}" height="8" rx="4" fill="{BAR_FILL}"/>
        <text x="{list_x_pct}" y="{y}" text-anchor="end" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{percent:.0f}%</text>
        '''
    )

other_percent = other_count / display_total * 100
other_progress = min((other_count / max_count) * bar_width, bar_width)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="bgGlow" x1="0" y1="0" x2="{WIDTH}" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0c1118"/>
      <stop offset="50%" stop-color="#0f1723"/>
      <stop offset="100%" stop-color="#0c1118"/>
    </linearGradient>
    <filter id="glow" x="-200%" y="-200%" width="400%" height="400%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="url(#bgGlow)" stroke="{BORDER}"/>

  <path d="M23 25 L28 13 L33 25 L46 26 L36 34 L39 46 L28 39 L17 46 L20 34 L10 26 Z"
        fill="none" stroke="{TITLE}" stroke-width="1.8" stroke-linejoin="round"/>
  <text x="52" y="34" fill="{TITLE}" font-size="22" font-weight="600" font-family="Segoe UI, Arial, sans-serif">Étoiles par pays</text>

  <text x="{WIDTH - 54}" y="32" text-anchor="end" fill="{MUTED}" font-size="11" font-family="Segoe UI, Arial, sans-serif">Répartition géographique des étoiles de mes dépôts</text>
  <circle cx="{WIDTH - 24}" cy="26" r="9" fill="none" stroke="{MUTED}" stroke-width="1.4" opacity="0.9"/>
  <text x="{WIDTH - 24}" y="30" text-anchor="middle" fill="{MUTED}" font-size="11" font-family="Segoe UI, Arial, sans-serif">i</text>

  <rect x="14" y="48" width="{WIDTH - 28}" height="{HEIGHT - 64}" rx="7" fill="none" stroke="{INNER_BORDER}"/>

  <line x1="545" y1="66" x2="545" y2="{HEIGHT - 20}" stroke="{INNER_BORDER}"/>

  {''.join(world_paths)}

  <g filter="url(#glow)">
    {''.join(point_svg)}
  </g>

  <rect x="34" y="225" width="132" height="46" rx="7" fill="#101722" stroke="{INNER_BORDER}"/>
  <text x="47" y="242" fill="{MUTED}" font-size="9" font-family="Segoe UI, Arial, sans-serif">Nombre d’étoiles</text>

  <circle cx="48" cy="256" r="2" fill="{GLOW}"/>
  <circle cx="74" cy="256" r="3.5" fill="{GLOW}"/>
  <circle cx="101" cy="256" r="5" fill="{GLOW}"/>
  <circle cx="133" cy="256" r="7.5" fill="{GLOW}"/>

  <text x="48" y="269" text-anchor="middle" fill="{MUTED}" font-size="8" font-family="Segoe UI, Arial, sans-serif">1</text>
  <text x="74" y="269" text-anchor="middle" fill="{MUTED}" font-size="8" font-family="Segoe UI, Arial, sans-serif">10</text>
  <text x="101" y="269" text-anchor="middle" fill="{MUTED}" font-size="8" font-family="Segoe UI, Arial, sans-serif">50</text>
  <text x="133" y="269" text-anchor="middle" fill="{MUTED}" font-size="8" font-family="Segoe UI, Arial, sans-serif">100+</text>

  {''.join(rows_svg)}

  <line x1="{list_x_rank}" y1="256" x2="950" y2="256" stroke="{INNER_BORDER}"/>

  <text x="{list_x_rank + 2}" y="281" fill="{TEXT}" font-size="16" font-family="Segoe UI Emoji, Segoe UI, Arial">🌐</text>
  <text x="{list_x_name}" y="281" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">Autres pays</text>
  <text x="{list_x_value}" y="281" text-anchor="end" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{format_number(other_count)}</text>
  <rect x="{list_x_bar}" y="271" width="{bar_width}" height="8" rx="4" fill="{BAR_BG}"/>
  <rect x="{list_x_bar}" y="271" width="{other_progress:.1f}" height="8" rx="4" fill="{BAR_FILL}"/>
  <text x="{list_x_pct}" y="281" text-anchor="end" fill="{TEXT}" font-size="12" font-family="Segoe UI, Arial, sans-serif">{other_percent:.0f}%</text>
</svg>
'''

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Generated {OUTPUT}")
