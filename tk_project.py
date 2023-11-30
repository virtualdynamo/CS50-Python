# tk_project.py
# Crowd sourced digital elevation model

# https://docs.python.org/3/library/pathlib.html
from pathlib import Path

from datetime import datetime
import csv

import numpy as np

import matplotlib.pyplot as plt

from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import askyesno

import gps_xml
import gps_math


def main():
    # Prompt user to specify course file and folder containing activities to study. All must be gpx files.
    course_file = get_course_file("gpx")
    course_df = gps_xml.get_course_df(course_file)
    activities = get_activities()

    start_exec = datetime.now()

    # Delete csv outputs from previous run.
    delete_csvs()

    # Get the latitude and longitude of the start and finish of the course
    start, finish = course_ends(course_df)

    plot_legend = []
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
            nice_activity_name = activity.stem.replace("_", " ").replace('"', " ")
            if last_row:
                # If successive enpdoints cross the start then the finish, this lap executed the course in the forward direction.
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
                    plot_legend.append(f"{nice_activity_name} FWD {forward+reverse+1}")
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
                    plot_legend.append(f"{nice_activity_name} REV {forward+reverse+1}")
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

        with open("project/csv_output/sec_laps.csv", "a", newline="") as f:
            fieldnames = ["Forward", "Beginning", "Ending", "Activity", "Lap_Index"]
            writer = csv.DictWriter(f, fieldnames)
            writer.writerows(sec_laps)

    # Output course dataframe to a csv file.
    course_df.to_csv("project/csv_output/course_ele.csv")

    # Write the elevation from the activity for each course point of each lap.
    with open("project/csv_output/laps_ele_raw.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(laps_ele_raw)

    # Write the interpolated elevations for each course point.
    with open("project/csv_output/laps_ele_inter.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(laps_ele_inter)

    laps_ele_raw_mean = np.array(laps_ele_raw).mean(0)
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

    course_stem = Path(course_file).stem    
    # Plot the raw elevation from the activities.
    plot_laps(
        course_df,
        laps_ele_raw_mean,
        laps_ele_raw,
        plot_legend,
        f"Raw runs - {course_stem}",
    )
    # Plot the interpolate elevation from the activities.
    plot_laps(
        course_df,
        laps_ele_inter_mean,
        laps_ele_inter,
        plot_legend,
        f"Benchmarked runs - {course_stem}",
    )


# Prompt user to specify course file  to study. Must be gpx files.
def get_course_file(file_type) -> str:
    answer = False
    while not answer:
        fileName = filedialog.askopenfilename(
            initialdir="project\\courses",
            title="Select a course file",
            filetypes=[(file_type.lower() + " files", "*." + file_type)],
        )
        if fileName:
            return fileName
        else:
            answer = askyesno(
                "Confirmation", "Are you sure you want to quit the program?"
            )
    exit(f"User aborted program when specifying {file_type} course file.")


# Get the latitude and longitude of the start and finish of the course.
def course_ends(course_df):
    start = point(course_df, 0)
    finish = point(course_df, -1)
    return start, finish


# Get the latitude and longitude of the point.
def point(df, i):
    return df.iloc[i]["lat"], df.iloc[i]["lon"]


# Prompt user to specify folder containing activities to study. Only gpx files will be processed.
def get_activities() -> []:
    answer = False
    while not answer:
        folder_name = filedialog.askdirectory(
            initialdir="project", title="Select folder with activities to study"
        )
        if folder_name:
            activities = list(Path(folder_name).glob("*.gpx"))
            if len(activities):
                print(f"Found {len(activities)} activity files in: {folder_name}")
                return activities
            else:
                exit("No gpx files in " + folder_name + " directory.")

        else:
            answer = askyesno(
                "Confirmation", "Are you sure you want to quit the program?"
            )
    exit("User aborted program when specifying activities folder.")


# Delete csv outputs from previous run.
def delete_csvs():
    files = list(Path("project/csv_output").glob("*.csv"))
    for file in files:
        file.unlink()


def custom_activity(f):
    return f"Working activity file: {f}"


def custom_laps(f, r):
    return f"\tLaps found: forward {f} reverse {r}"


def plot_laps(df, ele_mean, ele, legend, title):
    plt.plot(df["distance"], df["ele"], linestyle="dashed", label="Course")
    plt.plot(df["distance"], ele_mean, linestyle="dashdot", label="Average")
    for row in range(len(ele)):
        plt.plot(df["distance"], ele[row], label=legend[row])
    plt.title(title)
    plt.legend()
    plt.ylabel("Elevation (m)")
    plt.xlabel("Distance (km)")
    plt.show()
    pass


if __name__ == "__main__":
    main()
