# Weather CLI
A terminal based weather forecast tool built Python and Rich

## Features:
- Fetches 2 days of weather data from Open Meteo
- Displays results using Rich
- Response caching using requests-cache
- Retry logic (might update this later)
- Coordinates passed through argparse

## Installation
```
bash
git clone https://github.com/Lyzanov/weather-cli
cd weather-cli
pip install -r requirements.txt
```

## Usage
```
bash
python weather.py -lat (latitude coordinates) -long (longitude coordinates)
```

## Tech Stack
- Python
- [Rich](https://github.com/textualize/rich) for  live, panels, and rich text
- [Open-Meteo API](https://open-meteo.com/) for weather data
- openmeteo-requests - Open Meteo's official python client
- requests cache - response caching

## License
MIT
