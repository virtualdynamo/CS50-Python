# Crowdsourced digital elevation model--CS50 Python Final Project
#### Video Demo: <https://www.youtube.com/watch?v=DIrrdSBLFRU>
#### Description
This program uses crowdsourcing to produce a high quality digital elevation model (DEM) of a course. The DEMs for routing programs are rooted in the Shuttle Radar Topography Mission (SRTM) https://www2.jpl.nasa.gov/srtm/. Any such DEM has serious shortcomings for cycling. Especially when the DEM is a gauge for effort or accomplishemt. Barometric altimiters in GPSs do a good job of calculatinng relative changes in elevation. However, they rely on an external reference to ascertain absolute elevation of dubious quality and are subject to drift. By getting the GPS elevation of several runs between 2 known points of elevation, with a little math, a high quality DEM can be produced.

In addition to the requisite project.py, there is a nearly identical tk_project.py. The project.py version uses command line arguments to get user input for the program. The program outputs 4 CSV files that the user can subsequently study in Excel or the like. The tk_project.py version uses tkinter to get user input using a graphical user interface. It outputs the same CSV files as the command line version, but also displays a couple of matplotlib graphs,

# project.py

command-line:
python project.py -c course.GPX -a activity_folder
or
python project.py --course course.GPX --activities activity_folder

### main()
Read a course GPX file into a dataframe.
Read activity GPX fiies, one a time, into a dataframe.
Detect laps and their direction.
For each lap, find the activity time closest to each course trackpoint.
For each lap, lookup the elevation from the activity for each course trackpoint from the previous step.
Benchmark elevations for each lap to the course endpoints.
Output 4 CSV files:
1) sec_laps.csv: List of dictionaries of laps. Fields include lap direction, time crossing the beginning of the course, time crossing the ending of the course, activity	name, and lap index within activity.
2) course_ele.csv: Course dataframe. Fields include trackpoint index, latitude, longitude, elevation, and distance.
3) laps_ele_raw.csv: Array of raw lap elevations. Each row is for a lap. Each column is for a course trackpoint.
4) laps_ele_inter.csv: Array of benchmarked lap elevations. Each row is for a lap. Each column is for a course trackpoint.

### arguments():
Parses command-line arguements. Returns course and activities strings as argparse.ArgumentParser.parse_args() attributes.

### get_course(course):
Validate command-line specifed course file to study. Must be gpx file. Program exits if no course was specified, specified file was not a GPX, or file does not exist. Returns course file as pathlib.Path.

### course_ends(course_df):
Get the latitude and longitude of the start and finish of the course. Returns start and finish as point.

### point(df, i):
Get the latitude and longitude of row i in the dataframe. Returns 2 floating point values.

### get_activities(folder_name):
Validate command-line specifed folder containing activities to study. Only gpx files will be processed. Program exits if path does not exist or there are no gpx files in the folder. Returns activities in folder as a list of pathlib.Path.

### delete_csvs():
Delete all csv files in csv_output folder.

### custom_activity(f):
Lame function to satisfy requirement for "3 required custom functions other than main must also be in project.py". Returns an f-string of the activity being studied for output to the terminal.

### custom_laps(f, r):
Another lame function to satisfy requirement for "3 required custom functions other than main must also be in project.py". Returns an f-string of the count of forward and reverse laps for output to the terminal.

# tk_project.py DIFFERENCES from project.py

### main()
Uses tkinter graphical user interface in lieu of command-line arguments for specifying the course file and activities folderr. At the end of the program, matplotlab graphs of the lap raw elevation and lap benchmarked elevation are displayed.

### arguments(): NOT INCLUDED

### get_course_file(file_type) -> str: in lieu of get_course(course):
tkinter is used to prompt the user for the course GPX file. The user is given a chance to exit the program. Returns course filename.

### course_ends(course_df): IDENTICAL

### point(df, i): IDENTICAL

### get_activities() -> []: a little different
tkinter is used to prompt the user for the activities folder. The user is given a chance to exit the program. If the selected folder has no GPX files, the program exits. If there are GPX file, the funciton returns a list of activity files file as pathlib.Path.

### delete_csvs(): IDENTICAL

### custom_activity(f): IDENTICAL

### custom_laps(f, r): IDENTICAL

### plot_laps(df, ele_mean, ele, legend, title):
Uses matplotlab to graph elevation vs course distance for each lap, the average of the laps, and the course.

# gps_math.py

### haversine_laps(activity_df, course_df, sec_laps):
For each lap, finds the closest activity trackpoint for each course trackpoint. Returns a numpy array with the number of course trackpoints columns and number of laps rows.

### ele_raw(course_indices, activity_df, course_len, sec_laps):
Lookup the elevation from the activity for each course point of each lap. Returns a numpy array with the number of course trackpoints columns and number of laps rows.

### ele_inter(activity_df, course_df, sec_laps, laps_ele_raw):
Interpolate the elevation of the laps_ele_raw array by benchmarking to the endpoints of the course for each lap. Returns a numpy array with the number of course trackpoints columns and number of laps rows.

### total_climb(course_points):
Does a piecewise summation of all positive differences in elevations to calculate the climbing on the course. Returns the climbing and descending of the course.

### haversine_np(lon1, lat1, lon2, lat2):
Calculates the distance between 2 points on the surface of the earth. A radius of 6367 km is assumed. Returns distance in km. I had hoped to use the haversine package for all haversine calculations, but I couldn't readily figure out how to pass dataframe elements to haversine.
https://en.wikipedia.org/wiki/Haversine_formula 

# gps_xml.py

### get_gpx_df(xmlfile):
Reads a GPX file that builds a list of dictionaries with keys of lat, lon, and ele. Converts list to a dataframe and returns the dataframe.

### get_course_df(xmlfile):
Calls get_gpx_df to get the course into a dataframe and adds a column for distance. Uses the law of haversines to calculate the distance between course trackpoints. Calculates the distance along the course from the start to the respective course trackpoint. Returns the dataframe.

### get_activity_df(xmlfile, start, finish):
Calls get_gpx_df to get the activity into a dataframe and adds columns for start_dist, finish_dist, is_start, and is_finish. Uses the law of haversines to calculate the distance each activity trackpoint and the start. Does the same for the finish. Scans start_dist to find local minimums less than a threshold value and declares is_start to be true in those cases. Does the same for finish_dist/is_finish. Returns the dataframe.

# Dependencies
#### argparse
[argparse](https://docs.python.org/3/library/argparse.html) The argparse module makes it easy to write user-friendly command-line interfaces. 
#### pathlib
[pathlib](https://docs.python.org/3/library/pathlib.html) This module offers classes representing filesystem paths with semantics appropriate for different operating systems.
#### datetime
[datetime](https://docs.python.org/3/library/datetime.html) The datetime module supplies classes for manipulating dates and times.
#### csv
[csv](https://docs.python.org/3/library/csv.html) The so-called CSV (Comma Separated Values) format is the most common import and export format for spreadsheets and databases. 
#### numpy
[numpy](https://numpy.org/) NumPy is an open source project that enables numerical computing with Python. 
#### xml.etree.ElementTree
[xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html) The xml.etree.ElementTree module implements a simple and efficient API for parsing and creating XML data.
#### pandas
[pandas](https://pandas.pydata.org/) pandas aims to be the fundamental high-level building block for doing practical, real world data analysis in Python.
#### haversine
[haversine](https://pypi.org/project/haversine/) Calculate the distance (in various units) between two points on Earth using their latitude and longitude.
#### matplotlib.pyplot ONLY for tk_project.py
[matplotlib.pyplot](https://matplotlib.org/3.5.3/api/_as_gen/matplotlib.pyplot.html) matplotlib.pyplot is a state-based interface to matplotlib. It provides an implicit, MATLAB-like, way of plotting. It also opens figures on your screen, and acts as the figure GUI manager.
#### tkinter ONLY for tk_project.py
[tkinter](https://docs.python.org/3/library/tkinter.html) The tkinter package (“Tk interface”) is the standard Python interface to the Tcl/Tk GUI toolkit. Both Tk and tkinter are available on most Unix platforms, including macOS, as well as on Windows systems.
