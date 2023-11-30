# gps_math.py

import numpy as np

# For each trkpt in the course, find the closest activity trkpt using the law of haversines.
def haversine_laps(activity_df, course_df, sec_laps):
    course_indices = np.empty((len(sec_laps), len(course_df)), dtype=np.int64)
    for row, lap in enumerate(sec_laps):
        sec = lap["Beginning"]
        if lap["Forward"]:
            for course_index in range(len(course_df)):
                print(
                    f"\tLap: {row+1} of {len(sec_laps)} {(course_index+1)/len(course_df)*100:,.0f}%",
                    end="\r",
                )
                first_index = True
                while sec <= lap["Ending"]:
                    test_distance = haversine_np(
                        course_df.iloc[course_index]["lat"],
                        course_df.iloc[course_index]["lon"],
                        activity_df.iloc[sec]["lat"],
                        activity_df.iloc[sec]["lon"],
                    )
                    if first_index:
                        min_distance = test_distance
                        min_index = sec
                        first_index = False
                    if test_distance < min_distance:
                        min_distance = test_distance
                        min_index = sec
                    if test_distance > min_distance * 10 or sec == lap["Ending"]:
                        sec = min_index
                        course_indices[row][course_index] = sec
                        break
                    sec += 1
        else:
            for course_index in range(len(course_df)):
                print(
                    f"\tLap: {row+1} of {len(sec_laps)} {(course_index+1)/len(course_df)*100:,.0f}%",
                    end="\r",
                )
                first_index = True
                while sec >= lap["Ending"]:
                    test_distance = haversine_np(
                        course_df.iloc[course_index]["lat"],
                        course_df.iloc[course_index]["lon"],
                        activity_df.iloc[sec]["lat"],
                        activity_df.iloc[sec]["lon"],
                    )
                    if first_index:
                        min_distance = test_distance
                        min_index = sec
                        first_index = False
                    if test_distance < min_distance:
                        min_distance = test_distance
                        min_index = sec
                    if test_distance > min_distance * 10 or sec == lap["Ending"]:
                        sec = min_index
                        course_indices[row][course_index] = sec
                        break
                    sec -= 1
    print()

    return course_indices


# Lookup the elevation from the activity for each course point of each lap.
def ele_raw(course_indices, activity_df, course_len, sec_laps):
    laps_ele_raw = np.empty((len(sec_laps), course_len))
    for row, lap in enumerate(sec_laps):
        for course_index in range(course_len):
            laps_ele_raw[row][course_index] = activity_df.iloc[
                course_indices[row][course_index]
            ]["ele"]
    return laps_ele_raw

# Interpolate elevations using course enpoints as benchmarks.
def ele_inter(activity_df, course_df, sec_laps, laps_ele_raw):
    laps_ele_inter = np.empty((len(sec_laps), len(course_df)))
    x_delta = course_df.iloc[-1]["distance"] - course_df.iloc[0]["distance"]
    for row, lap in enumerate(sec_laps):
        offset_start = (
            course_df.iloc[0]["ele"] - activity_df.iloc[lap["Beginning"]]["ele"]
        )
        offset_finish = (
            course_df.iloc[-1]["ele"] - activity_df.iloc[lap["Ending"]]["ele"]
        )
        for course_index in range(len(course_df)):
            laps_ele_inter[row][course_index] = (
                laps_ele_raw[row][course_index]
                + offset_start
                + (offset_finish - offset_start)
                * (
                    course_df.iloc[course_index]["distance"]
                    - course_df.iloc[0]["distance"]
                )
                / x_delta
            )
    return laps_ele_inter


def total_climb(elevations):
    deltas = np.diff(elevations)
    climb = sum(delta for delta in deltas if delta > 0)
    return(climb, climb-elevations[-1]+elevations[0])

# The following function was stolen in whole from
# https://itecnote.com/tecnote/python-fast-haversine-approximation-python-pandas/
def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km
