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
    
    with open("data/gtfs_rail.zip", 'wb') as zip_out:
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

            stop_adj[prev_id][stop["stop_id"]].append(weight/60.0)

    return stop_adj 

def station_loc():
    """ Build a dictionary of station location"""
    loc_dict = {}
    
    with open("data/stops.txt") as stops:
        reader = csv.DictReader(stops)
        for line in reader:
            stop_id = line["stop_id"]
            lat = float(line["stop_lat"])
            lon = float(line["stop_lon"])
            
            loc_dict[stop_id] = (lat, lon)
    return loc_dict

def plot_times(stop_list, names):
    """Plot with whiskers"""

    x_list = range(len(stop_list))

    # Compute the values...
    y_list = [np.median(x) for x in stop_list]
    y_min = [np.min(x) for x in stop_list]
    y_max = [np.max(x) for x in stop_list]

    plt.plot(x_list, y_list)

    plt.xticks(x_list, names, rotation=75)

    plt.ylabel("Time from Previous (Minutes)")
    plt.xlabel("Destination")    


    plt.savefig("interstation_time.png", bbox_inches="tight")

    plt.show()

def main():
    # Get the full matrix
    adj_mat = build_stop_adj()

    # Get the stop locations
    stop_loc = station_loc()

    # Get the stuff for the expo line
    expo_stops = ["80122", "80121", "80123", "80124", "80125", "80126", "80127",
                  "80128", "80129", "80130", "80131", "80132", "80133", "80134",
                  "80135", "80136", "80137", "80138", "80139"]

    inter_time = []
    inter_speed = []
    inter_distance = []

    for index, stop in enumerate(expo_stops):
        if index == 0:
            continue
        
        # Figure out the time between
        time_list = adj_mat[expo_stops[index - 1]][stop]
        inter_time.append(time_list)

        # Figure out straightline distance, compute speed
        start_station = expo_stops[index-1]
        loc_a = stop_loc[start_station]
        loc_b = stop_loc[stop]

        # Wildly inaccurate eucidian distance
        distance = np.sqrt((loc_a[0] - loc_b[0])**2 + (loc_a[1] - loc_b[1])**2)

        inter_distance.append(distance)
   
        inter_speed.append(distance/np.median(time_list))

    # Plot 'em
    for index, list_entry in enumerate(inter_time):
        print(expo_stops[index+1], np.min(list_entry), np.max(list_entry))

    min_total = sum((np.min(x) for x in inter_time))
    max_total = sum((np.max(x) for x in inter_time))

    print(min_total, max_total)

    plot_times(inter_time, expo_stops)
    
