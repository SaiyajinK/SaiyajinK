import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

USERNAME = "SaiyajinK"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "profile-summary-card-output/custom/activity-3y.svg"

WIDTH = 620
HEIGHT = 220

REQUEST_DELAY = 2.2
MAX_RETRIES = 5

months = []
now = datetime.now(timezone.utc)

year = now.year
month = now.month

# 36 mois = 3 années
for offset in range(35, -1, -1):
    m = month - offset
    y = year

    while m <= 0:
        m += 12
        y -= 1

    months.append((y, m))


def github_request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USERNAME,
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    for attempt in range(MAX_RETRIES):
        request = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as error:
            if error.code not in (403, 429):
                raise

            retry_after = error.headers.get("Retry-After")
            rate_reset = error.headers.get("X-RateLimit-Reset")
            rate_remaining = error.headers.get("X-RateLimit-Remaining")

            if retry_after:
                wait_time = int(retry_after) + 2

            elif rate_remaining == "0" and rate_reset:
                reset_time = int(rate_reset)
                wait_time = max(
                    reset_time - int(time.time()) + 2,
                    5,
                )

            else:
                wait_time = 15 * (attempt + 1)

            print(
                f"GitHub returned HTTP {error.code}. "
                f"Waiting {wait_time}s before retry "
                f"({attempt + 1}/{MAX_RETRIES})..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        "GitHub API request failed after multiple retries."
    )


values = []

for index, (y, m) in enumerate(months):
    if m == 12:
        next_y = y + 1
        next_m = 1
    else:
        next_y = y
        next_m = m + 1

    start = f"{y:04d}-{m:02d}-01"
    end = f"{next_y:04d}-{next_m:02d}-01"

    query = (
        f"author:{USERNAME} "
        f"committer-date:{start}..{end}"
    )

    encoded = urllib.parse.quote(query)

    url = (
        "https://api.github.com/search/commits"
        f"?q={encoded}&per_page=1"
    )

    print(
        f"Fetching {y:04d}-{m:02d} "
        f"({index + 1}/{len(months)})..."
    )

    data = github_request(url)

    values.append(
        data.get("total_count", 0)
    )

    if index < len(months) - 1:
        time.sleep(REQUEST_DELAY)


max_value = max(values) if values else 1

if max_value == 0:
    max_value = 1

plot_left = 52
plot_right = WIDTH - 22
plot_top = 72
plot_bottom = HEIGHT - 34

plot_width = plot_right - plot_left
plot_height = plot_bottom - plot_top


def x_pos(index):
    if len(values) == 1:
        return plot_left + (plot_width / 2)

    return plot_left + (
        index * plot_width / (len(values) - 1)
    )


def y_pos(value):
    return plot_bottom - (
        value / max_value * plot_height * 0.85
    )


points = [
    (x_pos(i), y_pos(value))
    for i, value in enumerate(values)
]


def smooth_path(points):
    if not points:
        return ""

    path = (
        f"M {points[0][0]:.2f},"
        f"{points[0][1]:.2f}"
    )

    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]

        middle = (x0 + x1) / 2

        path += (
            f" C {middle:.2f},{y0:.2f}"
            f" {middle:.2f},{y1:.2f}"
            f" {x1:.2f},{y1:.2f}"
        )

    return path


line_path = smooth_path(points)

area_path = (
    line_path
    + f" L {points[-1][0]:.2f},{plot_bottom}"
    + f" L {points[0][0]:.2f},{plot_bottom} Z"
)

vertical_grid = []

for i in range(len(months)):
    x = x_pos(i)

    vertical_grid.append(
        f'''
        <line
            x1="{x:.2f}"
            y1="{plot_top}"
            x2="{x:.2f}"
            y2="{plot_bottom}"
            stroke="#26384c"
            stroke-width="1"
            stroke-dasharray="2 4"
            opacity="0.25"
        />
        '''
    )

major_year_lines = []
year_labels = []

seen_years = set()

for i, (y, m) in enumerate(months):
    if y not in seen_years:
        seen_years.add(y)

        x = x_pos(i)

        major_year_lines.append(
            f'''
            <line
                x1="{x:.2f}"
                y1="{plot_top}"
                x2="{x:.2f}"
                y2="{plot_bottom}"
                stroke="#35506d"
                stroke-width="1"
                opacity="0.85"
            />
            '''
        )

for target_year in sorted(set(y for y, _ in months)):
    indices = [
        i
        for i, (y, _) in enumerate(months)
        if y == target_year
    ]

    if not indices:
        continue

    first_index = indices[0]
    last_index = indices[-1]

    center_x = (
        x_pos(first_index)
        + x_pos(last_index)
    ) / 2

    year_labels.append(
        f'''
        <text
            x="{center_x:.2f}"
            y="{HEIGHT - 12}"
            text-anchor="middle"
            fill="#9da7b3"
            font-size="11"
            font-family="Segoe UI, Arial, sans-serif"
        >{target_year}</text>
        '''
    )

ticks = []

for fraction in [0, 1 / 3, 2 / 3, 1]:
    value = round(max_value * fraction)

    y = plot_bottom - (
        fraction * plot_height * 0.85
    )

    ticks.append(
        f'''
        <text
            x="34"
            y="{y + 4:.2f}"
            text-anchor="end"
            fill="#9da7b3"
            font-size="10"
            font-family="Segoe UI, Arial, sans-serif"
        >{value}</text>
        '''
    )

svg = f'''<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
    <defs>
        <linearGradient
            id="activityFill3Y"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
        >
            <stop
                offset="0%"
                stop-color="#536dfe"
                stop-opacity="0.30"
            />
            <stop
                offset="100%"
                stop-color="#536dfe"
                stop-opacity="0.03"
            />
        </linearGradient>

        <linearGradient
            id="activityLine3Y"
            x1="0"
            y1="0"
            x2="1"
            y2="0"
        >
            <stop
                offset="0%"
                stop-color="#398bff"
            />
            <stop
                offset="100%"
                stop-color="#895cff"
            />
        </linearGradient>
    </defs>

    <rect
        x="0.5"
        y="0.5"
        width="{WIDTH - 1}"
        height="{HEIGHT - 1}"
        rx="6"
        fill="#0d1117"
        stroke="#30363d"
    />

    <text
        x="20"
        y="31"
        fill="#008cff"
        font-size="19"
        font-weight="600"
        font-family="Segoe UI, Arial, sans-serif"
    >Activity</text>

    <text
        x="{WIDTH - 20}"
        y="31"
        text-anchor="end"
        fill="#9da7b3"
        font-size="11"
        font-family="Segoe UI, Arial, sans-serif"
    >Commits over the last 3 years</text>

    {''.join(vertical_grid)}
    {''.join(major_year_lines)}
    {''.join(ticks)}

    <path
        d="{area_path}"
        fill="url(#activityFill3Y)"
    />

    <path
        d="{line_path}"
        fill="none"
        stroke="url(#activityLine3Y)"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
    />

    {''.join(year_labels)}
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

print(f"Generated {OUTPUT}")
