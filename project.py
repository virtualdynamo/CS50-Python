# project.py
# Crowd sourced digital elevation model

# https://docs.python.org/3/library/argparse.html
import argparse

# https://docs.python.org/3/library/pathlib.html
from pathlib import Path

from datetime import datetime
import csv

import numpy as np

import gps_math
import gps_xml

def main():
    # Retrieve course file and folder containing activities to study. All must be gpx files.
    args = arguments()
    course_file = args.course
    activities_folder = args.activities

    course_df = gps_xml.get_course_df(get_course(course_file))
    activities = get_activities(activities_folder)

    start_exec = datetime.now()

    # Delete csv outputs from previous run.
    delete_csvs()

    # Get the latitude and longitude of the start and finish of the course
    start, finish = course_ends(course_df)

    laps_ele_raw = []
    laps_ele_inter = []

    # Process each activity file found.
    for activity in activities:
        print(custom_activity(activity))
        activity_df = gps_xml.get_activity_df(activity, start, finish)

        # Make a study of all course endpoints in the activity.
        activity_ends_df = activity_df.query("is_start or is_finish")
        sec_laps = []
        last_row = 0
        forward = 0
        reverse = 0
        for row, end in activity_ends_df.iterrows():
            if last_row:
                # If successive endpoints cross the start then the finish, this lap executed the course in the forward direction.
                if last_end["is_start"] and end["is_finish"]:
                    sec_laps.append(
                        {
                            "Forward": True,
                            "Beginning": last_row,
                            "Ending": row,
                            "Activity": activity.stem,
                            "Lap_Index": forward,
                        }
                    )
                    forward += 1
                # If successive endpoints cross the finish then the start, this lap executed the course in the reverse direction.
                elif last_end["is_finish"] and end["is_start"]:
                    sec_laps.append(
                        {
                            "Forward": False,
                            "Beginning": row,
                            "Ending": last_row,
                            "Activity": activity.stem,
                            "Lap_Index": reverse,
                        }
                    )
                    reverse += 1
                print(custom_laps(forward, reverse), end="\r")
            last_row = row
            last_end = end

        print()
        course_indices = gps_math.haversine_laps(activity_df, course_df, sec_laps)

        # Lookup the elevation from the activity for each course point of each lap.
        activity_laps_ele_raw = gps_math.ele_raw(
            course_indices, activity_df, len(course_df), sec_laps
        )
        for row in range(len(sec_laps)):
            laps_ele_raw.append(activity_laps_ele_raw[row])

        # Interpolate elevations using course endpoints as benchmarks.
        activity_laps_ele_inter = gps_math.ele_inter(
            activity_df, course_df, sec_laps, activity_laps_ele_raw
        )
        for row in range(len(sec_laps)):
            laps_ele_inter.append(activity_laps_ele_inter[row])

        with open("csv_output/sec_laps.csv", "a", newline="") as f:
            fieldnames = ["Forward", "Beginning", "Ending", "Activity", "Lap_Index"]
            writer = csv.DictWriter(f, fieldnames)
            writer.writerows(sec_laps)

    # Output course dataframe to a csv file.
    course_df.to_csv("csv_output/course_ele.csv")

    # Write the elevation from the activity for each course point of each lap.
    with open("csv_output/laps_ele_raw.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(laps_ele_raw)

    # Write the interpolated elevations for each course point.
    with open("csv_output/laps_ele_inter.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(laps_ele_inter)

    laps_ele_inter_mean = np.array(laps_ele_inter).mean(0)

    climb, descend = gps_math.total_climb(laps_ele_inter_mean)
    print(
        f"Total climbing: {climb:.2f}. Total descending: {descend:.2f}. Net ascent: {climb-descend:.2f}"
    )

    laps_ele_inter_stddev = np.std(
        laps_ele_inter_mean - np.array(course_df["ele"]), ddof=1
    )
    print(
        f"Standard deviation of the differnce between the course and average: {laps_ele_inter_stddev:.2f}"
    )

    end_exec = datetime.now()
    print(end_exec - start_exec)

# Parses command-line arguements of course file and activity folder.
def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course", help="Course .gpx file", type=str)
    parser.add_argument(
        "-a",
        "--activities",
        default="activities",
        help="Subdirectory with gpx activity files",
        type=str,
    )
    return parser.parse_args()


# Validate command-line specifed course file to study. Must be gpx file.
def get_course(course):
    if course:
        course_path = Path("courses/" + course)
        if Path(course_path).suffix == ".gpx":
            if course_path.is_file():
                return course_path
            else:
                exit(course + " does not exist in courses directory.")
        else:
            exit(course + " is not a gpx file.")
    else:
        exit("No course file was specified on the command line.")


# Get the latitude and longitude of the start and finish of the course.
def course_ends(course_df):
    start = point(course_df, 0)
    finish = point(course_df, -1)
    return start, finish


# Get the latitude and longitude of the point.
def point(df, i):
    return df.iloc[i]["lat"], df.iloc[i]["lon"]


# Validate command-line specifed folder containing activities to study. Only gpx files will be processed.
def get_activities(folder_name):
    activity_path = Path(folder_name)
    if activity_path.exists():
        activities = list(activity_path.glob("*.gpx"))
        if len(activities):
            print(f"Found {len(activities)} activity files in: {folder_name}")
            return activities
        else:
            exit("No gpx files in " + folder_name + " directory.")
    else:
        exit(folder_name + " does not exist.")


# Delete csv outputs from previous run.
def delete_csvs():
    files = list(Path("project/csv_output").glob("*.csv"))
    for file in files:
        file.unlink()


def custom_activity(f):
    return f"Working activity file: {f}"


def custom_laps(f, r):
    return f"\tLaps found: forward {f} reverse {r}"


if __name__ == "__main__":
    main()
