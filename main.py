""" Add a comment """
from PIL import Image
import gpxpy
import gpxpy.gpx
from datetime import datetime
from datetime import timedelta
import time
import os
import piexif
from fractions import Fraction
from photmetadata import PhotoMetadata
import photmetadata


# EXIF magic numbers from CIPA DC-008-Translation-2012
DateTimeOriginal = 36867
DateTimeDigitized = 36868

# System specific path
if os.name == 'nt':
    path = "D:\\Pictures\\2021\\2021_Test_AddlestoneMorningWalk"
else:
    path = '/Users/lawrence/Pictures/Photos/2021/2021_Test_AddlestoneMorningWalk'

# Time correction to apply to photo time
correction_seconds = 0
correction = timedelta(0, correction_seconds)

# Controls if metadata should be updated
update_exif = True

# path = '/Users/lawrence/Pictures/Photos/2021/2021_03_AddlestoneWalk'
osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'



def match_locations(gpx_xml, photo_data):
    """For each photo record, find the co-ordinates for the matching time from the gpx data
    If a correction is set apply it to the photo time (for when camera time was set wrong).
    :param gpx_xml: gpx data
    :type gpx_xml: xml
    :type photo_data: PhotoMetadata[]
    """
    # Variables
    photo_count = 0

    # Parse to gpx and iterate through
    input_gpx = gpxpy.parse(gpx_xml)
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_time = time.localtime(point.time.timestamp())
                # Apply correction
                photo_data[photo_count].timestamp += correction
                photo_time = time.localtime(photo_data[photo_count].timestamp.timestamp())
                # May be many photos at one point
                while point_time > photo_time and photo_count < len(photo_data):
                    photo_data[photo_count].set_gps(point.latitude, point.longitude, point.elevation)

                    # Next one
                    photo_count += 1
                    if photo_count >= len(photo_data):
                        break
                    photo_data[photo_count].timestamp += correction
                    photo_time = time.localtime(photo_data[photo_count].timestamp.timestamp())

                if photo_count >= len(photo_data):
                    break

    print('%s matched out of %s' % (photo_count, len(photo_data)))
    # Log correction used and result
    with open(path + '/location.txt', 'w') as logfile:
        logfile.write('%s\nPath = %s\nCorrection = %d sec\n%d matched out of %d' %
                      (datetime.now(),
                       path,
                       correction_seconds,
                       photo_count,
                       len(photo_data)))

    return


def get_exif_data():

    # Build list photos with date taken from exif metadata
    photo_data = []
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
            rec = PhotoMetadata(os.path.basename(entry.path), datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"))
            photo_data.append(rec)
    # Sort list by date/time
    photo_data.sort()

    # match photo location matching photo time and write results to csv
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            with open(entry.path, 'r') as file:
                gpx_data = file.read()
            match_locations(gpx_data, photo_data)
            with open(entry.path.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
                csv_file.write('Photo,Date/Time,Lat,Long,Link,Location\n')
                for record in photo_data:
                    csv_file.write(record.csv_output())



if __name__ == '__main__':
    get_exif_data()

