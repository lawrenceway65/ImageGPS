""""Test displaying image"""
import os
from PIL import Image
from PIL.ExifTags import TAGS
import gpxpy
import gpxpy.gpx
from datetime import datetime
import time
import os
import subprocess
import json


path = '/Users/lawrence/Pictures/Photos/2021/2021_04_Byfleet'


def get_locality(latitude, longitude):
    """Get location from co-ordinates. Use Open Street Map.
    Using street level (zoom = 16) and picking second item, gives more accurate result
    """
    osm_request = "https://nominatim.openstreetmap.org/reverse?lat=%f&lon=%f&zoom=20&format=json"
    #   print(OSMRequest % (Latitude, Longitude))
    result = subprocess.check_output(['curl', '-s', osm_request % (latitude, longitude)]).decode("utf-8")
    result_json = json.loads(result)

    # Extract second item from 'display_name'
    return result_json['display_name']


def get_locations(gpx_xml, photos):
    """For each photo record find the co-ordinated for the matching time from the gpx data

    :param gpx_xml: gpx data
    :type gpx_xml: xml
    """
    # Variables
    photo_count = 0
    output_data = 'Photo,Date/Time,Lat,Long,Location\n'

    # Parse to gpx and iterate through
    input_gpx = gpxpy.parse(gpx_xml)
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_time = time.localtime(point.time.timestamp())
                rec = photos[photo_count]
                photo_time = time.localtime(photos[photo_count][0].timestamp())
                if point_time > photo_time:
                    locality = get_locality(point.latitude, point.longitude)
                    s = '%s,%s,%f,%f,%s\n' % (photos[photo_count][1],
                                                      photos[photo_count][0].strftime('%d:%m:%Y %H:%M:%S'),
                                                      point.latitude,
                                                      point.longitude,
                                                      get_locality(point.latitude, point.longitude))
                    print(s)
                    output_data += s
                    photo_count += 1
                if photo_count >= len(photos):
                    break

    return output_data


def get_exif_data():
    list = []
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            image = Image.open(entry.path)
            exif = image.getexif()
            for tag, value in exif.items():
                if TAGS.get(tag, tag) == 'DateTimeOriginal':
                    rec = (datetime.strptime(value, "%Y:%m:%d %H:%M:%S"), os.path.basename(entry.path))
                    list.append(rec)
                    break

    list.sort()
#    for item in list:
#        print(item)

    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            with open(entry.path, 'r') as file:
                gpx_data = file.read()
            csv_data = get_locations(gpx_data, list)
            with open(path + '/locations.csv', 'w') as csv_file:
                csv_file.write(csv_data)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    get_exif_data()

