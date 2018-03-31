""" Main for python analysis stuff"""

import csv
import datetime
import os
import os.path
import requests
import zipfile

import numpy as np

from matplotlib import pyplot as plt

def fetch():
    """ Fetch the latest gtfs data"""
    # Do we have a data folder?
    if not os.path.isdir("data"):
        os.mkdir("data")

    # go ahead and grab the latest file, weather we have it or not
    print("Fetching latest...")
    response = requests.get("https://gitlab.com/LACMTA/gtfs_rail/raw/master/gtfs_rail.zip")

    response.raise_for_status()
    
    with open("data/gtfs_rail.zip", 'w') as zip_out:
        for block in response.iter_content(1024):
            zip_out.write(block)         

    print("Unzipping...")
    # Let's unzip that shit
    zip_ref = zipfile.ZipFile("data/gtfs_rail.zip", 'r')
    zip_ref.extractall("data/")
    zip_ref.close()

def build_stop_adj():
    """Load GTFS data and plot interstation times for expo"""

    # Let's load up that stops file times
    stop_times = {}
    with open("data/stop_times.txt") as stop_times_file:
        reader = csv.DictReader(stop_times_file)

        # Spin through the lines
        for line in reader:
            # Get the trip_id
            trip_id = line["trip_id"]

            # did we have this?
            if trip_id not in stop_times:
                stop_times[trip_id] = []

            # Add it to the list
            stop_times[trip_id].append(line)

    # Sort them all by sequence number. Probably we could do that at insert,
    # but fuck it
    for trip in stop_times:
        stop_times[trip].sort(key=lambda x: int(x["stop_sequence"]))

    # Build a dumb adjacencey matrix
    stop_adj = {}

    for trip in stop_times:
        curr_trip = stop_times[trip]
        # Loop through the seq of stops
        for index, stop in enumerate(curr_trip):
            # If its the first one, just move on
            if index == 0:
                continue

            # Where did I come from?
            prev = curr_trip[index - 1]
            prev_id = prev["stop_id"]

            # Put it in adj matrix if needed
            if prev_id not in stop_adj:
                stop_adj[prev_id] = {}

            # What's the time between the two?
            # TODO Getting hacky with time, assuming no DST silly
            depart_components = prev["departure_time"].split(":")
            depart_components[0] = str(int(depart_components[0]) % 24)
            depart_time = datetime.datetime.strptime(":".join(depart_components),
                                                     "%H:%M:%S")
            arrive_components = stop["arrival_time"].split(":")
            arrive_components[0] = str(int(arrive_components[0]) % 24)
            arrive_string = ":".join(arrive_components)
            arrive_time = datetime.datetime.strptime(arrive_string,
                                                     "%H:%M:%S")

            # TODO: That mod to deal with day wrap around is real sketchy
            weight = (arrive_time - depart_time).total_seconds() % 86400

            # Stick it in the matrix
            if stop["stop_id"] not in stop_adj[prev_id]:
                stop_adj[prev_id][stop["stop_id"]] = []

            stop_adj[prev_id][stop["stop_id"]].append(weight)

    return stop_adj 

def plot_whiskers(stop_list):
    """Plot with whiskers"""

    x_list = xrange(stop_list)
    y_list = [np.median(x) for x in stop_list]

    plt.plot(x_list, y_list)

    plt.show()

def main():
    # Get the full matrix
    adj_mat = build_stop_adj()

    # Get the stuff for the expo line
    expo_stops = ["80122", "80121", "80123", "80124", "80125", "80126", "80127",
                  "80128", "80129", "80130", "80131", "80132", "80133", "80134",
                  "80135", "80136", "80137", "80138", "80139"]

    inter_time = []

    for index, stop in enumerate(expo_stops):
        if index == 0:
            continue

        time_list = adj_mat[expo_stops[index - 1]][stop]

        inter_time.append(time_list)

    # Plot 'em
    for index, list_entry in enumerate(inter_time):
        print expo_stops[index+1], np.min(list_entry), np.max(list_entry)

    min_total = sum((np.min(x) for x in inter_time))
    max_total = sum((np.max(x) for x in inter_time))

    print min_total/60.0, max_total/60.0

    plot_whiskers(inter_time)
