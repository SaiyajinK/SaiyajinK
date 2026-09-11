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

# Vraie carte SVG Robinson / SimpleMaps
WORLD_MAP_URL = (
    "https://simplemaps.com/static/demos/"
    "resources/svg-library/svgs/world.svg"
)

# Drapeaux SVG
FLAG_URL = (
    "https://raw.githubusercontent.com/"
    "lipis/flag-icons/main/flags/4x3/{code}.svg"
)

BG = "#0d1117"
BORDER = "#30363d"
INNER_BORDER = "#26384c"

TITLE = "#008cff"
TEXT = "#c9d1d9"
MUTED = "#8b9bb0"

MAP_FILL = "#142131"
MAP_STROKE = "#263d58"

BLUE = "#438cff"
BAR_BG = "#192638"

POINT = "#6678ff"
POINT_CORE = "#d1d8ff"

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required")


# ------------------------------------------------------------
# GitHub
# ------------------------------------------------------------

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
        request,
        timeout=60,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]


# ------------------------------------------------------------
# Download
# ------------------------------------------------------------

def download_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "SaiyajinK-GitHub-Profile/1.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:
        return response.read().decode("utf-8")


# ------------------------------------------------------------
# Cache géolocalisation
# ------------------------------------------------------------

def load_cache():
    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)
    except Exception:
        return {}


def save_cache(cache):
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
            cache,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ------------------------------------------------------------
# Localisation -> pays
# ------------------------------------------------------------

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

    url = (
        "https://nominatim.openstreetmap.org/"
        "search?"
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
            timeout=30,
        ) as response:
            results = json.loads(
                response.read().decode("utf-8")
            )

    except Exception as error:
        print(
            f"Geocoding failed for "
            f"{location}: {error}"
        )

        cache[location] = None
        return None

    if not results:
        cache[location] = None
        return None

    address = results[0].get(
        "address",
        {},
    )

    result = {
        "country_code": (
            address.get("country_code")
            or ""
        ).upper(),

        "country_name": (
            address.get("country")
            or ""
        ),
    }

    cache[location] = result

    # Respect Nominatim
    time.sleep(1.05)

    return result


# ------------------------------------------------------------
# GitHub : étoiles
# ------------------------------------------------------------

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
        location
      }
    }
  }
}
"""


repos_data = graphql(
    repos_query,
    {"login": USERNAME},
)

repos = [
    repo
    for repo
    in repos_data["user"]["repositories"]["nodes"]
    if repo["stargazerCount"] > 0
]


raw_locations = Counter()


for repo in repos:
    repo_name = repo["name"]

    print(
        f"Reading stars from "
        f"{repo_name}..."
    )

    after = None

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
                raw_locations[location] += 1

        page = stars["pageInfo"]

        if not page["hasNextPage"]:
            break

        after = page["endCursor"]


# ------------------------------------------------------------
# Résolution pays
# ------------------------------------------------------------

cache = load_cache()

country_counts = Counter()
country_names = {}


for index, (
    location,
    count,
) in enumerate(
    raw_locations.most_common(),
    start=1,
):
    print(
        f"Geocoding {index}/"
        f"{len(raw_locations)}: "
        f"{location}"
    )

    geo = geocode_location(
        location,
        cache,
    )

    if not geo:
        continue

    code = geo["country_code"]

    if len(code) != 2:
        continue

    country_counts[code] += count

    country_names[code] = (
        geo["country_name"]
        or code
    )


save_cache(cache)


# ------------------------------------------------------------
# Vrai template SimpleMaps
# ------------------------------------------------------------

print("Downloading SimpleMaps world template...")

world_svg_text = download_text(
    WORLD_MAP_URL
)

ET.register_namespace(
    "",
    "http://www.w3.org/2000/svg",
)

world_root = ET.fromstring(
    world_svg_text
)

viewbox = world_root.get(
    "viewBox",
    "0 0 1000 507",
)

vb = [
    float(value)
    for value in viewbox.split()
]

VB_X = vb[0]
VB_Y = vb[1]
VB_W = vb[2]
VB_H = vb[3]


# ------------------------------------------------------------
# Nettoyage graphique + centres des pays
# ------------------------------------------------------------

country_boxes = {}


def add_bbox(code, bbox):
    xmin, xmax, ymin, ymax = bbox

    if code not in country_boxes:
        country_boxes[code] = [
            xmin,
            xmax,
            ymin,
            ymax,
        ]
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

    if tag not in (
        "path",
        "polygon",
        "polyline",
    ):
        continue

    element.set(
        "fill",
        MAP_FILL,
    )

    element.set(
        "stroke",
        MAP_STROKE,
    )

    element.set(
        "stroke-width",
        "0.7",
    )

    element.attrib.pop(
        "style",
        None,
    )

    if tag != "path":
        continue

    d = element.get("d")

    if not d:
        continue

    code = (
        element.get("id")
        or ""
    ).upper()

    if len(code) != 2:
        continue

    try:
        bbox = parse_path(d).bbox()
        add_bbox(
            code,
            bbox,
        )
    except Exception:
        pass


# ------------------------------------------------------------
# Contenu SVG du template
# ------------------------------------------------------------

world_inner = "".join(
    ET.tostring(
        child,
        encoding="unicode",
    )
    for child in list(world_root)
)


# ------------------------------------------------------------
# Bulles proportionnelles
# ------------------------------------------------------------

max_stars = max(
    country_counts.values(),
    default=1,
)

bubble_svg = []


for code, count in country_counts.items():
    if code not in country_boxes:
        continue

    xmin, xmax, ymin, ymax = (
        country_boxes[code]
    )

    cx = (
        xmin + xmax
    ) / 2

    cy = (
        ymin + ymax
    ) / 2

    ratio = (
        count / max_stars
    )

    radius = (
        7
        + math.sqrt(ratio) * 24
    )

    bubble_svg.append(
        f'''
        <circle
            cx="{cx:.2f}"
            cy="{cy:.2f}"
            r="{radius * 2.1:.2f}"
            fill="{POINT}"
            opacity="0.08"
        />

        <circle
            cx="{cx:.2f}"
            cy="{cy:.2f}"
            r="{radius * 1.45:.2f}"
            fill="{POINT}"
            opacity="0.15"
        />

        <circle
            cx="{cx:.2f}"
            cy="{cy:.2f}"
            r="{radius:.2f}"
            fill="{POINT}"
            opacity="0.78"
        />

        <circle
            cx="{cx:.2f}"
            cy="{cy:.2f}"
            r="{max(2.5, radius * 0.18):.2f}"
            fill="{POINT_CORE}"
        />
        '''
    )


# ------------------------------------------------------------
# Flags inline
# ------------------------------------------------------------

flag_cache = {}


def flag_svg(code, x, y):
    code = code.lower()

    if code not in flag_cache:
        try:
            source = download_text(
                FLAG_URL.format(
                    code=code
                )
            )

            root = ET.fromstring(
                source
            )

            flag_viewbox = root.get(
                "viewBox",
                "0 0 640 480",
            )

            inner = "".join(
                ET.tostring(
                    child,
                    encoding="unicode",
                )
                for child in list(root)
            )

            flag_cache[code] = (
                flag_viewbox,
                inner,
            )

        except Exception:
            flag_cache[code] = None

    result = flag_cache[code]

    if not result:
        return (
            f'<text x="{x}" y="{y + 12}" '
            f'fill="{MUTED}" '
            f'font-size="10">'
            f'{code.upper()}</text>'
        )

    flag_viewbox, inner = result

    return f'''
    <svg
        x="{x}"
        y="{y}"
        width="19"
        height="14"
        viewBox="{flag_viewbox}"
        preserveAspectRatio="xMidYMid slice"
    >
        {inner}
    </svg>
    '''


# ------------------------------------------------------------
# Classement
# ------------------------------------------------------------

top_countries = (
    country_counts.most_common(5)
)

resolved_total = sum(
    country_counts.values()
)

top_total = sum(
    count
    for _, count
    in top_countries
)

other_count = max(
    resolved_total - top_total,
    0,
)

display_total = max(
    resolved_total,
    1,
)

top_max = max(
    [
        count
        for _, count
        in top_countries
    ]
    or [1]
)


def number(value):
    if value >= 1000:
        result = (
            f"{value / 1000:.1f}k"
        )
        return result.replace(
            ".0k",
            "k",
        )

    return str(value)


rows = []

ROW_Y = 76
ROW_GAP = 25

for index, (
    code,
    count,
) in enumerate(
    top_countries,
    start=1,
):
    y = (
        ROW_Y
        + (index - 1)
        * ROW_GAP
    )

    percent = (
        count
        / display_total
        * 100
    )

    bar_width = (
        count
        / top_max
        * 72
    )

    country_name = (
        country_names.get(
            code,
            code,
        )
    )

    rows.append(
        f'''
        <text
            x="410"
            y="{y}"
            fill="{MUTED}"
            font-size="10"
            font-family="Segoe UI, Arial, sans-serif"
        >{index}</text>

        {flag_svg(code, 428, y - 12)}

        <text
            x="454"
            y="{y}"
            fill="{TEXT}"
            font-size="10.5"
            font-family="Segoe UI, Arial, sans-serif"
        >{country_name}</text>

        <text
            x="544"
            y="{y}"
            text-anchor="end"
            fill="{TEXT}"
            font-size="10"
            font-family="Segoe UI, Arial, sans-serif"
        >{number(count)}</text>

        <rect
            x="557"
            y="{y - 8}"
            width="72"
            height="7"
            rx="3.5"
            fill="{BAR_BG}"
        />

        <rect
            x="557"
            y="{y - 8}"
            width="{bar_width:.2f}"
            height="7"
            rx="3.5"
            fill="{BLUE}"
        />

        <text
            x="638"
            y="{y}"
            text-anchor="end"
            fill="{TEXT}"
            font-size="10"
            font-family="Segoe UI, Arial, sans-serif"
        >{percent:.0f}%</text>
        '''
    )


other_percent = (
    other_count
    / display_total
    * 100
)

other_bar = min(
    (
        other_count
        / top_max
        * 72
    ),
    72,
)


# ------------------------------------------------------------
# SVG final
# ------------------------------------------------------------

svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>

    <defs>
        <linearGradient
            id="cardBg"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
        >
            <stop
                offset="0%"
                stop-color="#0d1117"
            />

            <stop
                offset="100%"
                stop-color="#101722"
            />
        </linearGradient>
    </defs>

    <rect
        x="0.5"
        y="0.5"
        width="{WIDTH - 1}"
        height="{HEIGHT - 1}"
        rx="7"
        fill="url(#cardBg)"
        stroke="{BORDER}"
    />

    <!-- Étoile -->
    <path
        d="
        M20 12
        L23.6 22
        L34 22.3
        L25.8 28.7
        L28.8 39
        L20 33
        L11.2 39
        L14.2 28.7
        L6 22.3
        L16.4 22 Z
        "
        fill="none"
        stroke="{TITLE}"
        stroke-width="1.7"
        stroke-linejoin="round"
    />

    <text
        x="43"
        y="31"
        fill="{TITLE}"
        font-size="17"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >Étoiles par pays</text>

    <text
        x="615"
        y="29"
        text-anchor="end"
        fill="{MUTED}"
        font-size="8.5"
        font-family="Segoe UI, Arial, sans-serif"
    >Répartition géographique des étoiles de mes dépôts</text>

    <circle
        cx="632"
        cy="25"
        r="7"
        fill="none"
        stroke="{MUTED}"
        stroke-width="1"
    />

    <text
        x="632"
        y="28"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="8"
        font-family="Segoe UI, Arial, sans-serif"
    >i</text>

    <rect
        x="13"
        y="45"
        width="624"
        height="172"
        rx="6"
        fill="none"
        stroke="{INNER_BORDER}"
    />

    <!-- vraie carte Robinson, aucune déformation -->
    <svg
        x="20"
        y="55"
        width="365"
        height="150"
        viewBox="{viewbox}"
        preserveAspectRatio="xMidYMid meet"
    >
        {world_inner}

        {''.join(bubble_svg)}
    </svg>

    <!-- Légende -->
    <rect
        x="28"
        y="167"
        width="104"
        height="41"
        rx="5"
        fill="#101722"
        stroke="{INNER_BORDER}"
    />

    <text
        x="37"
        y="181"
        fill="{MUTED}"
        font-size="7"
        font-family="Segoe UI, Arial, sans-serif"
    >Nombre d’étoiles</text>

    <circle
        cx="40"
        cy="193"
        r="2"
        fill="{POINT}"
    />

    <circle
        cx="62"
        cy="193"
        r="3.2"
        fill="{POINT}"
    />

    <circle
        cx="87"
        cy="193"
        r="5"
        fill="{POINT}"
    />

    <circle
        cx="116"
        cy="193"
        r="8"
        fill="{POINT}"
    />

    <text
        x="40"
        y="204"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="6"
        font-family="Segoe UI, Arial, sans-serif"
    >1</text>

    <text
        x="62"
        y="204"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="6"
        font-family="Segoe UI, Arial, sans-serif"
    >10</text>

    <text
        x="87"
        y="204"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="6"
        font-family="Segoe UI, Arial, sans-serif"
    >50</text>

    <text
        x="116"
        y="204"
        text-anchor="middle"
        fill="{MUTED}"
        font-size="6"
        font-family="Segoe UI, Arial, sans-serif"
    >100+</text>

    <!-- séparation -->
    <line
        x1="397"
        y1="58"
        x2="397"
        y2="208"
        stroke="{INNER_BORDER}"
    />

    <!-- classement -->
    {''.join(rows)}

    <line
        x1="409"
        y1="192"
        x2="632"
        y2="192"
        stroke="{INNER_BORDER}"
    />

    <!-- autres pays -->
    <circle
        cx="429"
        cy="207"
        r="7"
        fill="none"
        stroke="{MUTED}"
        stroke-width="1"
    />

    <path
        d="
        M422 207 H436
        M429 200
        C425 203 425 211 429 214
        M429 200
        C433 203 433 211 429 214
        "
        fill="none"
        stroke="{MUTED}"
        stroke-width="0.8"
    />

    <text
        x="454"
        y="210"
        fill="{TEXT}"
        font-size="10.5"
        font-family="Segoe UI, Arial, sans-serif"
    >Autres pays</text>

    <text
        x="544"
        y="210"
        text-anchor="end"
        fill="{TEXT}"
        font-size="10"
        font-family="Segoe UI, Arial, sans-serif"
    >{number(other_count)}</text>

    <rect
        x="557"
        y="202"
        width="72"
        height="7"
        rx="3.5"
        fill="{BAR_BG}"
    />

    <rect
        x="557"
        y="202"
        width="{other_bar:.2f}"
        height="7"
        rx="3.5"
        fill="{BLUE}"
    />

    <text
        x="638"
        y="210"
        text-anchor="end"
        fill="{TEXT}"
        font-size="10"
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
