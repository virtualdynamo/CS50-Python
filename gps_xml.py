# gps_xml.py

import xml.etree.ElementTree as ET
import pandas as pd
from haversine import haversine

import gps_math

# https://www.youtube.com/watch?v=aB_koPUNqfo
# https://saturncloud.io/blog/converting-xml-to-python-dataframe-a-comprehensive-guide/


def get_gpx_df(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    trkpts = []
    for trkpt in root.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        trkpt_lat = float(trkpt.attrib["lat"])
        trkpt_lon = float(trkpt.attrib["lon"])
        trkpt_ele = float(trkpt.find("{http://www.topografix.com/GPX/1/1}ele").text)
        trkpts.append({"lat": trkpt_lat, "lon": trkpt_lon, "ele": trkpt_ele})

    df = pd.DataFrame(trkpts)
    return df


# Read course file and calculate course distance from start for each course point.
def get_course_df(xmlfile):
    df = get_gpx_df(xmlfile)
    df.insert(3, "distance", 0.0)
    for row in range(1, len(df)):
        df.loc[row, ("distance")] = (
            haversine(
                (df.loc[row, "lat"], df.loc[row, "lon"]),
                (df.loc[row - 1, "lat"], df.loc[row - 1, "lon"]),
            )
            + df.loc[row - 1, ("distance")]
        )
    return df


# Read activity file.
# For each trkpt: calculate  distance from course start and finish  and determine if point is at the start or finish of course.
def get_activity_df(xmlfile, start, finish):
    df = get_gpx_df(xmlfile)

    local_min_test = min(haversine((start[0], start[1]),(finish[0], finish[1]))*.01,0.03)
    df["start_dist"] = gps_math.haversine_np(df["lat"], df["lon"], start[0], start[1])
    df["finish_dist"] = gps_math.haversine_np(
        df["lat"], df["lon"], finish[0], finish[1]
    )

    df.insert(5, "is_start", False)
    df.insert(6, "is_finish", False)

    starts = finishes = 0
    for row in range(1, len(df) - 1):
        if df.loc[row]["start_dist"] < local_min_test:
            if (
                df.loc[row]["start_dist"] < df.loc[row - 1]["start_dist"]
                and df.loc[row]["start_dist"] < df.loc[row + 1]["start_dist"]
            ):
                df.loc[row, ("is_start")] = True
                starts+=1
                print(f"\tTotal of {starts} starts and {finishes} finishes found in activity.",end="\r")
        if df.loc[row]["finish_dist"] < local_min_test:
            if (
                df.loc[row]["finish_dist"] < df.loc[row - 1]["finish_dist"]
                and df.loc[row]["finish_dist"] < df.loc[row + 1]["finish_dist"]
            ):
                df.loc[row, ("is_finish")] = True
                finishes+=1
                print(f"\tTotal of {starts} starts and {finishes} finishes found in activity.",end="\r")
    print()
    return df
