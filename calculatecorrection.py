""""Test displaying image"""
import os
from PIL import Image
from PIL.ExifTags import TAGS
import gpxpy
import gpxpy.gpx
from geopy.distance import distance
from datetime import datetime
from datetime import timedelta
import time
import os
import subprocess
import json


if os.name == 'nt':
    path = "D:\\Pictures\\2021\\2021_Test_AddlestoneMorningWalk"
else:
    path = '/Users/lawrence/Pictures/Photos/2021/2021_01_HamptontoKingston'

osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'


def calculate_distance(point1, point2):
    """Wrapper for distance calculation
    Pass in gps points, return separation
    """
    coord1 = (point1.latitude, point1.longitude)
    coord2 = (point2.latitude, point2.longitude)

    return distance(coord1, coord2).meters


def get_difference(gpx_xml, photo_time, lat, long):
    """From gpx track find the difference between the time recirded and the actual time.
    Actual time is the time the point closest to the location was recorded.
    Required to correct for the fact camera time wasn't set correctly

    :param gpx_xml: gpx data
    :type gpx_xml: xml
    """
    min_separation = 9999
    reference_point = gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=long)

    # Parse to gpx and iterate through to find closest point to co-ordinates
    input_gpx = gpxpy.parse(gpx_xml)
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                separation = calculate_distance(point, reference_point)
                if separation < min_separation:
                    min_separation = separation
                    correction = point.time.timestamp() - photo_time.timestamp()

    if min_separation == 9999:
        print('Point not found')
        return 9999
    else:
        return correction


def calculate_correction():

    photo = 'IMG_6642.jpg'
    lat = 51.400984
    long = -0.34279

    # Get time photo taken from exif
    image = Image.open(path + '/' + photo)
    exif = image.getexif()
    for tag, value in exif.items():
        if TAGS.get(tag, tag) == 'DateTimeOriginal':
            photo_time = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            with open(entry.path, 'r') as gpx_file:
                gpx_data = gpx_file.read()
            correction = get_difference(gpx_data, photo_time, lat, long)
    print(correction)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    calculate_correction()

