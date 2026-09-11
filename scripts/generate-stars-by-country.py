import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = (
    "profile-summary-card-output/"
    "custom/stars-by-country.svg"
)

CACHE_FILE = (
    "profile-summary-card-output/"
    "custom/stars-country-cache.json"
)

WIDTH = 860
HEIGHT = 360

BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

BLUE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#9da7b3"

MAP_FILL = "#111d2c"
MAP_BORDER = "#243c59"

BAR_BG = "#192536"
BAR_FILL = "#438cff"

GLOW = "#6076ff"

MAX_MAP_POINTS = 35

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

    with urllib.request.urlopen(
        request
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    if "errors" in payload:
        raise RuntimeError(
            payload["errors"]
        )

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
        stargazerCount
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
    repo
    for repo
    in repo_data["user"]["repositories"]["nodes"]
    if repo["stargazerCount"] > 0
]


stars_query = """
query(
  $owner: String!,
  $name: String!,
  $after: String
) {
  repository(
    owner: $owner,
    name: $name
  ) {
    stargazers(
      first: 100,
      after: $after
    ) {
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


locations = Counter()

for repo in repos:
    repo_name = repo["name"]
    after = None

    print(
        f"Lecture des étoiles de "
        f"{repo_name}..."
    )

    while True:
        data = graphql(
            stars_query,
            {
                "owner": USERNAME,
                "name": repo_name,
                "after": after,
            },
        )

        stars = (
            data["repository"]
            ["stargazers"]
        )

        for user in stars["nodes"]:
            location = (
                user.get("location")
                or ""
            ).strip()

            if location:
                locations[location] += 1

        page = stars["pageInfo"]

        if not page["hasNextPage"]:
            break

        after = page["endCursor"]


try:
    with open(
        CACHE_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        geocode_cache = json.load(file)
except Exception:
    geocode_cache = {}


def geocode(location):
    if location in geocode_cache:
        return geocode_cache[location]

    params = urllib.parse.urlencode(
        {
            "q": location,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        }
    )

    url = (
        "https://nominatim."
        "openstreetmap.org/search?"
        + params
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "SaiyajinK-GitHub-Profile/1.0",
            "Accept-Language": "fr",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            result = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except Exception as error:
        print(
            f"Géocodage impossible pour "
            f"{location}: {error}"
        )

        geocode_cache[location] = None
        return None

    if not result:
        geocode_cache[location] = None
        return None

    item = result[0]

    address = item.get(
        "address",
        {},
    )

    country_code = (
        address.get("country_code")
        or ""
    ).upper()

    country_name = (
        address.get("country")
        or country_code
    )

    data = {
        "country_code": country_code,
        "country_name": country_name,
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
    }

    geocode_cache[location] = data

    time.sleep(1.05)

    return data


country_counts = Counter()
country_names = {}

point_counts = defaultdict(
    lambda: {
        "count": 0,
        "lat": 0.0,
        "lon": 0.0,
    }
)

resolved_stars = 0

for index, (
    location,
    count,
) in enumerate(
    locations.most_common()
):
    print(
        f"Géocodage {index + 1}/"
        f"{len(locations)} : "
        f"{location}"
    )

    geo = geocode(location)

    if not geo:
        continue

    code = geo["country_code"]

    if not code:
        continue

    country_counts[code] += count
    country_names[code] = (
        geo["country_name"]
    )

    resolved_stars += count

    rounded_lat = round(
        geo["lat"],
        1,
    )

    rounded_lon = round(
        geo["lon"],
        1,
    )

    key = (
        rounded_lat,
        rounded_lon,
    )

    point_counts[key]["count"] += count
    point_counts[key]["lat"] = (
        geo["lat"]
    )
    point_counts[key]["lon"] = (
        geo["lon"]
    )


os.makedirs(
    os.path.dirname(CACHE_FILE),
    exist_ok=True,
)

with open(
    CACHE_FILE,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        geocode_cache,
        file,
        ensure_ascii=False,
        indent=2,
    )


def flag(code):
    if len(code) != 2:
        return "🌐"

    return "".join(
        chr(
            127397 + ord(letter)
        )
        for letter in code.upper()
    )


def format_number(value):
    if value >= 1000:
        return (
            f"{value / 1000:.1f}k"
            .replace(".0k", "k")
        )

    return str(value)


top_countries = (
    country_counts.most_common(5)
)

top_total = sum(
    count
    for _, count
    in top_countries
)

other_count = max(
    resolved_stars - top_total,
    0,
)

display_total = max(
    resolved_stars,
    1,
)


# -------------------------
# Carte du monde
# -------------------------

MAP_X = 26
MAP_Y = 86
MAP_W = 468
MAP_H = 220


def project(lon, lat):
    x = (
        MAP_X
        + ((lon + 180) / 360)
        * MAP_W
    )

    y = (
        MAP_Y
        + ((90 - lat) / 180)
        * MAP_H
    )

    return x, y


world_paths = []

WORLD_URL = (
    "https://raw.githubusercontent.com/"
    "holtzy/D3-graph-gallery/master/"
    "DATA/world.geojson"
)

try:
    request = urllib.request.Request(
        WORLD_URL,
        headers={
            "User-Agent":
                "SaiyajinK-GitHub-Profile/1.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        world = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    for feature in world["features"]:
        geometry = feature.get(
            "geometry"
        )

        if not geometry:
            continue

        geometry_type = geometry["type"]
        coordinates = geometry[
            "coordinates"
        ]

        if geometry_type == "Polygon":
            polygons = [coordinates]

        elif geometry_type == "MultiPolygon":
            polygons = coordinates

        else:
            continue

        for polygon in polygons:
            for ring in polygon:
                if not ring:
                    continue

                commands = []

                for i, (
                    lon,
                    lat,
                ) in enumerate(ring):
                    x, y = project(
                        lon,
                        lat,
                    )

                    command = (
                        "M"
                        if i == 0
                        else "L"
                    )

                    commands.append(
                        f"{command}"
                        f"{x:.1f},"
                        f"{y:.1f}"
                    )

                commands.append("Z")

                world_paths.append(
                    '<path '
                    f'd="{" ".join(commands)}" '
                    f'fill="{MAP_FILL}" '
                    f'stroke="{MAP_BORDER}" '
                    'stroke-width="0.45"/>'
                )

except Exception as error:
    print(
        "Impossible de récupérer "
        f"la carte du monde: {error}"
    )


map_points = []

for (
    _,
    point,
) in sorted(
    point_counts.items(),
    key=lambda item:
        item[1]["count"],
    reverse=True,
)[:MAX_MAP_POINTS]:

    x, y = project(
        point["lon"],
        point["lat"],
    )

    count = point["count"]

    radius = min(
        3.5 + math.sqrt(count) * 1.25,
        12,
    )

    map_points.append(
        f'''
        <circle
            cx="{x:.1f}"
            cy="{y:.1f}"
            r="{radius * 2:.1f}"
            fill="{GLOW}"
            opacity="0.09"
        />

        <circle
            cx="{x:.1f}"
            cy="{y:.1f}"
            r="{radius:.1f}"
            fill="{GLOW}"
            opacity="0.85"
        />

        <circle
            cx="{x:.1f}"
            cy="{y:.1f}"
            r="2"
            fill="#b8c4ff"
        />
        '''
    )


# -------------------------
# Liste des pays
# -------------------------

ranking = []

list_x = 535
start_y = 112
row_gap = 38

max_country_count = max(
    [
        value
        for _, value
        in top_countries
    ]
    or [1]
)

for index, (
    code,
    count,
) in enumerate(
    top_countries
):
    y = (
        start_y
        + index * row_gap
    )

    name = country_names.get(
        code,
        code,
    )

    percent = (
        count
        / display_total
        * 100
    )

    progress = (
        count
        / max_country_count
        * 118
    )

    ranking.append(
        f'''
        <text
            x="{list_x}"
            y="{y}"
            fill="{MUTED}"
            font-size="12"
            font-family="Segoe UI, Arial, sans-serif"
        >{index + 1}</text>

        <text
            x="{list_x + 25}"
            y="{y}"
            fill="{TEXT}"
            font-size="17"
            font-family="Segoe UI Emoji, Segoe UI, Arial"
        >{flag(code)}</text>

        <text
            x="{list_x + 52}"
            y="{y}"
            fill="{TEXT}"
            font-size="12"
            font-family="Segoe UI, Arial, sans-serif"
        >{name}</text>

        <text
            x="{list_x + 180}"
            y="{y}"
            text-anchor="end"
            fill="{TEXT}"
            font-size="12"
            font-family="Segoe UI, Arial, sans-serif"
        >{format_number(count)}</text>

        <rect
            x="{list_x + 195}"
            y="{y - 10}"
            width="118"
            height="8"
            rx="4"
            fill="{BAR_BG}"
        />

        <rect
            x="{list_x + 195}"
            y="{y - 10}"
            width="{progress:.1f}"
            height="8"
            rx="4"
            fill="{BAR_FILL}"
        />

        <text
            x="{WIDTH - 25}"
            y="{y}"
            text-anchor="end"
            fill="{TEXT}"
            font-size="12"
            font-family="Segoe UI, Arial, sans-serif"
        >{percent:.0f}%</text>
        '''
    )


other_percent = (
    other_count
    / display_total
    * 100
)

other_progress = min(
    other_count
    / max_country_count
    * 118,
    118,
)


svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>

    <defs>
        <filter
            id="glow"
            x="-100%"
            y="-100%"
            width="300%"
            height="300%"
        >
            <feGaussianBlur
                stdDeviation="5"
                result="blur"
            />

            <feMerge>
                <feMergeNode
                    in="blur"
                />
                <feMergeNode
                    in="SourceGraphic"
                />
            </feMerge>
        </filter>
    </defs>

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
        y="38"
        fill="{BLUE}"
        font-size="22"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >Étoiles par pays</text>

    <text
        x="{WIDTH - 28}"
        y="37"
        text-anchor="end"
        fill="{MUTED}"
        font-size="11"
        font-family="Segoe UI, Arial, sans-serif"
    >Répartition géographique des étoiles de mes dépôts</text>

    <rect
        x="20"
        y="60"
        width="{WIDTH - 40}"
        height="{HEIGHT - 82}"
        rx="7"
        fill="{BG}"
        stroke="{INNER_BORDER}"
    />

    <line
        x1="510"
        y1="74"
        x2="510"
        y2="{HEIGHT - 36}"
        stroke="{INNER_BORDER}"
    />

    {''.join(world_paths)}

    <g filter="url(#glow)">
        {''.join(map_points)}
    </g>

    <rect
        x="35"
        y="270"
        width="155"
        height="60"
        rx="7"
        fill="#0c141f"
        stroke="{INNER_BORDER}"
    />

    <text
        x="47"
        y="289"
        fill="{MUTED}"
        font-size="10"
        font-family="Segoe UI, Arial, sans-serif"
    >Nombre d’étoiles</text>

    <circle
        cx="54"
        cy="310"
        r="2.5"
        fill="{GLOW}"
    />

    <circle
        cx="84"
        cy="310"
        r="4"
        fill="{GLOW}"
    />

    <circle
        cx="119"
        cy="310"
        r="6"
        fill="{GLOW}"
    />

    <circle
        cx="162"
        cy="310"
        r="9"
        fill="{GLOW}"
    />

    <text
        x="54"
        y="326"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="9"
        font-family="Segoe UI, Arial, sans-serif"
    >1</text>

    <text
        x="84"
        y="326"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="9"
        font-family="Segoe UI, Arial, sans-serif"
    >10</text>

    <text
        x="119"
        y="326"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="9"
        font-family="Segoe UI, Arial, sans-serif"
    >50</text>

    <text
        x="162"
        y="326"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="9"
        font-family="Segoe UI, Arial, sans-serif"
    >100+</text>

    {''.join(ranking)}

    <line
        x1="{list_x}"
        y1="300"
        x2="{WIDTH - 25}"
        y2="300"
        stroke="{INNER_BORDER}"
    />

    <text
        x="{list_x + 25}"
        y="325"
        fill="{TEXT}"
        font-size="12"
        font-family="Segoe UI, Arial, sans-serif"
    >🌐  Autres pays</text>

    <text
        x="{list_x + 180}"
        y="325"
        text-anchor="end"
        fill="{TEXT}"
        font-size="12"
        font-family="Segoe UI, Arial, sans-serif"
    >{format_number(other_count)}</text>

    <rect
        x="{list_x + 195}"
        y="315"
        width="118"
        height="8"
        rx="4"
        fill="{BAR_BG}"
    />

    <rect
        x="{list_x + 195}"
        y="315"
        width="{other_progress:.1f}"
        height="8"
        rx="4"
        fill="{BAR_FILL}"
    />

    <text
        x="{WIDTH - 25}"
        y="325"
        text-anchor="end"
        fill="{TEXT}"
        font-size="12"
        font-family="Segoe UI, Arial, sans-serif"
    >{other_percent:.0f}%</text>

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
