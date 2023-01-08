""""Test displaying image"""
import os
from PIL import Image
from PIL.ExifTags import TAGS
import gpxpy
import gpxpy.gpx
from geopy.distance import distance
from datetime import datetime
import os


class PointList:
    """Can be used for debug if issues with matching"""
    def __init__(self):
        self.min = 99999
        self.point_list = []
        self.getting_closer = True

    def new_point(self, point, distance, correction):
        add = False
        if len(self.point_list) < 10:
            add = True
        else:
            max_distance = 0
            max_index = 999
            index = 0
            for item in self.point_list:
                if item[0] > max_distance:
                    max_distance = item[0]
                    max_index = index
                index += 1
            if max_index != 999:
                add = True
                del self.point_list[max_index]

        if add:
            rec = (distance, point.latitude, point.longitude, correction)
            self.point_list.append(rec)


    def print_list(self):
        for rec in self.point_list:
            print("%f\t%f\t%f\t%d" % (rec[0], rec[1], rec[2], rec[3]))


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
    point_list = PointList()

    # Parse to gpx and iterate through to find closest point to co-ordinates
    input_gpx = gpxpy.parse(gpx_xml)
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                separation = calculate_distance(point, reference_point)
                point_list.new_point(point, separation, point.time.timestamp() - photo_time.timestamp())
                if separation < min_separation:
                    min_separation = separation
                    correction = point.time.timestamp() - photo_time.timestamp()

    if min_separation == 9999:
        print('Point not found')
        return 9999
    else:
        point_list.print_list()
        return correction


def calculate_correction(path, photo_file, gpx_filespec, lat, long):

    # Get time photo taken from exif
    image = Image.open(path + '/' + photo_file)
    exif = image.getexif()
    for tag, value in exif.items():
        if TAGS.get(tag, tag) == 'DateTimeOriginal':
            photo_time = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

    with open(gpx_filespec, 'r') as gpx_file:
        gpx_data = gpx_file.read()
    correction = get_difference(gpx_data, photo_time, lat, long)

    print(correction)
    return correction


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    calculate_correction()

