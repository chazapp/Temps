import os
import time
import json
import requests
from array import array
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv
from argparse import ArgumentParser
import pandas as pd
import numpy as np

"""
    temps.py: Create diagrams of a dataset of dates to temperature
    dataset.json:
    {
        "<event>": {
            "lat": <float>,
            "lon": <float>,
            "range": "<hour during day, each day>",
            "lines": " {
                "<line name>": {
                    "dates": [
                        "<ISO date>",
                        "<ISO date>"
                    ]
                }
            }
        }
    }

    This dataset will plot a line diagram for each provided line using data
    fetched via OpenWeatherMap API historical data.
    The resulting images are stored under `graphs/<event>.png `
"""

load_dotenv()
OPENWEATHERMAP_KEY = os.getenv("OPENWEATHERMAP_KEY")


def get_datapoints_from_api(lon: float, lat: float, range: array, lines: object):
    datapoints = {}
    for k, v in lines.items():
        datapoints[k] = {}
        for date in v["dates"]:
            datapoints[k][date] = []
            for point in range:
                datepoint = date + " " + point 
                ts = datetime.strptime(datepoint, "%Y-%m-%d %H:%M").timestamp()
                res = requests.get("https://api.openweathermap.org/data/3.0/onecall/timemachine", params={
                    "lat": lat,
                    "lon": lon,
                    "dt": int(ts),
                    "units": "metric",
                    "appid": OPENWEATHERMAP_KEY,
                })
                if res.status_code != 200:
                    print(res.status_code, res.content)
                    exit(1)
                temp = res.json()['data'][0]['temp']
                datapoints[k][date].append(temp)
    return datapoints

def plot_line_diagram(datapoints: object, name: str, range: array):
    dataset = {}
    for k, v in datapoints.items():
        year = []
        for day, values in v.items():
            year += values
        dataset[k] = year
    
    df = pd.DataFrame(
        dataset,
        index=range * 8
    )
    df.plot()
    x_ticks = np.arange(0, 48, 1, dtype=int)
    x_labels = range * 8
    plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
    plt.title("Temperature at Boom Festival")
    plt.ylabel("Temperature (°C)")
    plt.xlabel("Hour of the day")
    plt.show()
    pass


def get_datapoints_locally():
    try:
        with open("datapoints.json", "r") as fd:
            datapoints = json.loads(fd.read())
            return datapoints
    except IOError as e:
        print("Did not find datapoints. Reaching API...")

def save_datapoints_locally(datapoints):
    print("Saving API datapoints...")
    with open("datapoints.json", "w") as fd:
        fd.write(json.dumps(datapoints))
    pass


def load_points(path: str):
    graphs = None
    with open(path, "r") as fd:
        try: 
            graphs = json.loads(fd.read())
        except json.JSONDecodeError as e:
            print(e)
    for k,v in graphs.items():
        datapoints = get_datapoints_locally()
        if datapoints is None:
            datapoints = get_datapoints_from_api(v["lon"], v["lat"], v["range"], v["lines"])
            save_datapoints_locally(datapoints)
        graph = plot_line_diagram(datapoints, k, v["range"])
    pass

if __name__ == '__main__':
    print("Temperature comparator")
    parser = ArgumentParser(description="Temperature comparator")
    parser.add_argument("--data", type=str, required=True, help="The data to be fetched")
    args = parser.parse_args()
    load_points(args.data)