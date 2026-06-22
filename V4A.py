#!/home/lysanov/VSCodium-Python/.venv/bin/python3
from numpy import datetime_data, indices
import openmeteo_requests
import requests_cache
import datetime
import argparse

from time import sleep
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box
from rich.layout import Layout
from rich.live import Live
from datetime import datetime, timedelta
from retry_requests import retry

console = Console()


def parse_longlat():
    parser = argparse.ArgumentParser(
        description="Weather TUI - Fetch Weather Data Based on Coordinates"
    )
    parser.add_argument(
        "-lat",
        type=float,
        required=True,
        metavar="Latitude",
        help="Latitude of the location",
    )
    parser.add_argument(
        "-long",
        type=float,
        required=True,
        metavar="Longitude",
        help="Longitude of the location",
    )
    return parser.parse_args()


def dataFetch(lat, long):
    params = {
        "latitude": lat,
        "longitude": long,
        "hourly": [
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "rain",
            "uv_index",
            "weather_code",
        ],
        "minutely_15": ["temperature_2m", "apparent_temperature", "rain"],
        "timezone": "auto",
        "forecast_days": 2,
    }
    try:
        cache_session = requests_cache.CachedSession(".cacheV4A", expire_after=86400)
        retry_session = retry(cache_session, retries=5, backoff_factor=5)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        requests = openmeteo.weather_api(
            "https://api.open-meteo.com/v1/forecast", params=params
        )
        response = requests[0]
        minutely_15 = response.Minutely15()
        hourly = response.Hourly()
        cache_status = "Cached"
        return minutely_15, hourly, cache_status
    except Exception:
        stale_session = requests_cache.CachedSession(".cacheV4A", expire_after=-1)
        openmeteo_stale = openmeteo_requests.Client(session=stale_session)

        requests = openmeteo_stale.weather_api(
            "https://api.open-meteo.com/v1/forecast", params=params
        )
        response = requests[0]
        minutely_15 = response.Minutely15()
        hourly = response.Hourly()
        cache_status = "Stale Data"
        return minutely_15, hourly, cache_status
    except:
        return None, None, "Cache Empty"


def minutely_process(minutely_15):
    start = datetime.fromtimestamp(minutely_15.Time())
    end = datetime.fromtimestamp(minutely_15.TimeEnd())
    interval = timedelta(seconds=minutely_15.Interval())

    time = []
    current = start
    while current < end:
        time.append(current)
        current += interval

    temperature = minutely_15.Variables(0).ValuesAsNumpy()
    apparent = minutely_15.Variables(1).ValuesAsNumpy()
    rain = minutely_15.Variables(2).ValuesAsNumpy()

    return {
        "time": time,
        "temperature": temperature,
        "apparent": apparent,
        "rain": rain,
    }


def hourly_process(hourly):
    start = datetime.fromtimestamp(hourly.Time())
    end = datetime.fromtimestamp(hourly.TimeEnd())
    interval = timedelta(seconds=hourly.Interval())

    time = []
    current = start
    while current < end:
        time.append(current)
        current += interval

    temperature = hourly.Variables(0).ValuesAsNumpy()
    apparent = hourly.Variables(1).ValuesAsNumpy()
    precipitation = hourly.Variables(2).ValuesAsNumpy()
    rain = hourly.Variables(3).ValuesAsNumpy()
    uv = hourly.Variables(4).ValuesAsNumpy()
    code = hourly.Variables(5).ValuesAsNumpy()

    return {
        "time": time,
        "temperature": temperature,
        "apparent": apparent,
        "precipitation": precipitation,
        "rain": rain,
        "uv": uv,
        "code": code,
    }


def minutely_index():
    now = datetime.now()
    midnight = now.hour * 60 + now.minute
    indexm = midnight // 15
    return min(indexm, 94)


def hourly_index():
    now = datetime.now()
    current = now.hour
    indices = []
    for i in range(5):
        index = current + i
        indices.append(index)
    return indices


def codeDesc(code):
    codes = {
        0: "Clear Skies",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Foggy",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        61: "Slight Rain",
        63: "Slight Rain",
        65: "Moderate Rain",
        80: "Slight Rain Shower",
        81: "Moderate Rain Shower",
        82: "Violent Rain Shower",
        95: "Slight to Moderate Thunderstorm",
    }
    return codes.get(int(code), f"Code {int(code)}")


def temps_color(temps):
    temps = float(temps)
    if temps < 27:
        color = "blue"
    elif temps < 29:
        color = "cyan"
    elif temps < 32:
        color = "yellow"
    elif temps < 35:
        color = "orange1"
    else:
        color = "red"
    return color


def rain_color(rain):
    rain = float(rain)
    if rain == 0:
        color = "white"
    elif rain <= 1:
        color = "cyan"
    elif rain <= 2:
        color = "blue"
    else:
        color = "blue"
    return color


def precipitation_color(precip):
    precip = float(precip)
    if precip <= 20:
        color = "white"
    elif precip <= 49:
        color = "cyan"
    elif precip <= 75:
        color = "blue"
    else:
        color = "bold blue"
    return color


def uv_colors(uv):
    uv = float(uv)
    if uv <= 2:
        color = "green"
    elif uv <= 5:
        color = "yellow"
    elif uv <= 7:
        color = "orange1"
    elif uv <= 10:
        color = "red"
    else:
        color = "purple"
    return color


def uv_desc(uv):
    uv = float(uv)
    if uv <= 2:
        risk = "Low"
    elif uv <= 5:
        risk = "Moderate"
    elif uv <= 7:
        risk = "High"
    elif uv <= 10:
        risk = "Very High"
    else:
        risk = "Extreme"
    return risk


def build_header(indexm, indices, cache_status, lat, long):
    time = datetime.now().strftime("%I:%M:%S%p")
    panel = Panel(
        Text(
            f"Location: {lat}°N {long}°E -- Time: {time} -- Slots: |{indexm}|{indices[0]}| -- {cache_status}",
            style="bold white",
            justify="center",
        ),
        style="magenta",
        box=box.ROUNDED,
        title="[white]Weather TUI V4A[/white]",
    )
    return panel


def build_minutely(m, indexm):
    mtext = Text()
    mtext.append("Current Temperature: ", style="green")
    mtext.append(
        f"{m['temperature'][indexm]:.2f}°C\n",
        style=temps_color(m["temperature"][indexm]),
    )
    mtext.append("Apparent Temperature: ", style="green")
    mtext.append(
        f"{m['apparent'][indexm]:.2f}°C\n", style=temps_color(m["apparent"][indexm])
    )
    mtext.append("Rain Index: ", style="green")
    mtext.append(f"{m['rain'][indexm]:.2f}mm\n", style=rain_color(m["rain"][indexm]))

    mpanel = Panel(
        mtext,
        title="[white]15 Minutely Forecast[/white]",
        style="green",
        box=box.ROUNDED,
    )
    return mpanel


def build_uvwea(h, indices):
    code = codeDesc(h["code"][indices[0]])
    risk = uv_desc(h["uv"][indices[0]])

    uvwea = Text()
    uvwea.append("UV Index: ", style="green")
    uvwea.append(f"{h['uv'][indices[0]]:.2f}\n", style=uv_colors(h["uv"][indices[0]]))
    uvwea.append("Risk: ", style="green")
    uvwea.append(f"{risk}\n", style=uv_colors(h["uv"][indices[0]]))
    uvwea.append("Weather Conditions: ", style="green")
    uvwea.append(f"{code}", style="bold white")

    uvwea_pan = Panel(
        uvwea, style="orange1", title="[white]UV Monitor[/white]", box=box.ROUNDED
    )
    return uvwea_pan


def build_hourly(h, indices):
    temp_row = Text()
    apparent_row = Text()
    rain_row = Text()
    precip_row = Text()

    for i in indices:
        valt = float(h["temperature"][i])
        vala = float(h["apparent"][i])
        valr = float(h["rain"][i])
        valp = float(h["precipitation"][i])

        temp_row.append(f"{valt:.2f}°C", style=temps_color(valt))
        apparent_row.append(f"{vala:.2f}°C", style=temps_color(vala))
        rain_row.append(f"{valr:.2f}mm", style=rain_color(valr))
        precip_row.append(f"{valp:.2f}%", style=precipitation_color(valp))

        if i != indices[-1]:
            temp_row.append(" / ")
            apparent_row.append(" / ")
            rain_row.append(" / ")
            precip_row.append(" / ")

    time_strip = " / ".join(h["time"][i].strftime("%I:%M%p") for i in indices)

    htext = Text()
    htext.append("Time Forecast: ", style="green")
    htext.append(f"{time_strip}\n", style="white")
    htext.append("Temperature: ", style="green")
    htext.append_text(temp_row)
    htext.append("\n")
    htext.append("Apparent Temperatures: ", style="green")
    htext.append_text(apparent_row)
    htext.append("\n")
    htext.append("Precipitation: ", style="green")
    htext.append_text(precip_row)
    htext.append("\n")

    hourly_panel = Panel(
        htext, style="red", box=box.ROUNDED, title="[white]Hourly Data[/white]"
    )
    return hourly_panel


def build_layout(m, h, indexm, indices, cache_status, lat, long):
    header = build_header(indexm, indices, cache_status, lat, long)
    minutely = build_minutely(m, indexm)
    uvwea = build_uvwea(h, indices)
    hourly = build_hourly(h, indices)

    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="body"))
    layout["body"].split_column(Layout(name="upper"), Layout(name="bottom"))
    layout["upper"].split_row(Layout(name="minutely"), Layout(name="uv"))

    layout["header"].update(header)
    layout["minutely"].update(minutely)
    layout["uv"].update(uvwea)
    layout["bottom"].update(hourly)

    return layout


def main():
    args = parse_longlat()
    minutely_15, hourly, cache_status = dataFetch(args.lat, args.long)

    if minutely_15 == None:
        console.print("No data present. Exiting.", style="red")
        raise SystemExit(1)

    m = minutely_process(minutely_15)
    h = hourly_process(hourly)

    last_fetch = datetime.now()
    last_retry = datetime.now()

    indexm = minutely_index()
    indices = hourly_index()
    layout = build_layout(m, h, indexm, indices, cache_status, args.lat, args.long)

    last_index = None
    last_indice = None

    with Live(screen=True) as live:
        while True:
            now = datetime.now()
            if (now - last_fetch).total_seconds() >= 86400:
                cache_status = "Refreshing"
                layout["header"].update(
                    build_header(indexm, indices, cache_status, args.lat, args.long)
                )
                live.update(layout)
                minutely_15, hourly, cache_status = dataFetch(args.lat, args.long)

                if minutely_15 is not None:
                    m = minutely_process(minutely_15)
                    h = hourly_process(hourly)
                    last_fetch = now
                last_retry = now
            elif cache_status in ("stale", "offline"):
                if (now - last_retry).total_seconds() >= 3600:
                    cache_status = "Refreshing"
                    layout["header"].update(
                        build_header(indexm, indices, cache_status, args.lat, args.long)
                    )
                    live.update(layout)

                    minutely_15, hourly, cache_status = dataFetch(args.lat, args.long)
                    if minutely_15 is not None:
                        m = minutely_process(minutely_15)
                        h = hourly_process(hourly)
                        last_fetch = now
                    last_retry = now

            indexm = minutely_index()
            indices = hourly_index()

            if indexm != last_index or indices[0] != last_indice:
                layout = build_layout(
                    m, h, indexm, indices, cache_status, args.lat, args.long
                )
                last_index = indexm
                last_indice = indices[0]

            layout["header"].update(
                build_header(indexm, indices, cache_status, args.lat, args.long)
            )
            live.update(layout)
            sleep(1)


main()
