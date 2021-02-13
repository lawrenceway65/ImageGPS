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
    hardcoded_path = "D:\\Pictures\\2021\\2021_Test_AddlestoneMorningWalk"
else:
    hardcoded_path = '/Users/lawrence/Pictures/Photos/2021/2021_01_HamptontoKingston'

# Time correction to apply to photo time
correction_seconds = 0
correction = timedelta(0, correction_seconds)

osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'



def match_locations(gpx_xml, photo_data, path):
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
                corrected_time = photo_data[photo_count].timestamp + correction
                photo_time = time.localtime(corrected_time.timestamp())
                # May be many photos at one point
                while point_time > photo_time and photo_count < len(photo_data):
                    # Found a match so update
#                    print('Point: %s Photo(orig): %s Photo(corr): %s' % (point.time, photo_data[photo_count].timestamp, corrected_time))
                    photo_data[photo_count].timestamp = corrected_time
                    photo_data[photo_count].set_gps(point.latitude, point.longitude, point.elevation)
                    # Next one
                    photo_count += 1
                    if photo_count >= len(photo_data):
                        break
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

    return photo_count


def get_photo_data(path):
    """Build list photos with date taken from exif metadata
    Match photos to gpx track based on time and build list
    :param path: folder to analyse
    """
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
            match_locations(gpx_data, photo_data, path)
            with open(entry.path.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
                csv_file.write('Photo,Date/Time,Lat,Long,Link,Location\n')
                for record in photo_data:
                    csv_file.write(record.csv_output())



if __name__ == '__main__':
    get_photo_data(hardcoded_path)

