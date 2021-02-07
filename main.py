""""Test displaying image"""
import os
from PIL import Image
from PIL.ExifTags import TAGS
import gpxpy
import gpxpy.gpx
from datetime import datetime
from datetime import timedelta
import time
import os
import subprocess
import json
import piexif

# EXIF magic numbers from CIPA DC- 008-Translation- 2012
DateTimeOriginal = 36867
DateTimeDigitized = 36868


# System specific path
if os.name == 'nt':
    path = "D:\\Pictures\\2021\\2021_05_AddlestoneMorningWalk"
else:
    path = '/Users/lawrence/Pictures/Photos/2021/2021_06_ChertseyMeads'
# Time correction to apply to photo time
correction_seconds = 0
correction = timedelta(0, correction_seconds)

# path = '/Users/lawrence/Pictures/Photos/2021/2021_03_AddlestoneWalk'
osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'


def get_locality(latitude, longitude):
    """Get location from co-ordinates. Use Open Street Map.
    Using street level (zoom = 16) and picking second item, gives more accurate result
    """
    osm_request = "https://nominatim.openstreetmap.org/reverse?lat=%f&lon=%f&zoom=20&format=json"
    #   print(OSMRequest % (Latitude, Longitude))
    result = subprocess.check_output(['curl', '-s', osm_request % (latitude, longitude)]).decode("utf-8")
    result_json = json.loads(result)

    # Return full address for location ('display_name')
    return result_json['display_name']


def match_locations(gpx_xml, photos):
    """For each photo record, find the co-ordinates for the matching time from the gpx data
    If a correction is set apply it to the photo time (for when camera time was set wrong).
    :param gpx_xml: gpx data
    :type gpx_xml: xml
    """
    # Variables
    photo_count = 0
    output_data = 'Photo,Date/Time,Lat,Long,Link,Location\n'

    # Parse to gpx and iterate through
    input_gpx = gpxpy.parse(gpx_xml)
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_time = time.localtime(point.time.timestamp())
                # Apply correction
                corrected_photo_time = photos[photo_count][0] + correction
                photo_time = time.localtime(corrected_photo_time.timestamp())
                # May be many photos at one point
                while point_time > photo_time and photo_count < len(photos):
                    osm_link = osm_location_format % (point.latitude, point.longitude, point.latitude, point.longitude)
                    s = '%s,%s,%f,%f,"%s","%s"' % (photos[photo_count][1],
                                                   corrected_photo_time.strftime('%d:%m:%Y %H:%M:%S'),
                                                   point.latitude,
                                                   point.longitude,
                                                   osm_link,
                                                   get_locality(point.latitude, point.longitude))
                    print(s)
                    output_data += s
                    output_data += '\n'
                    # Next one
                    photo_count += 1
                    if photo_count >= len(photos):
                        break
                    corrected_photo_time = photos[photo_count][0] + correction
                    photo_time = time.localtime(corrected_photo_time.timestamp())

                if photo_count >= len(photos):
                    break

    print('%s matched out of %s' % (photo_count, len(photos)))
    # Log correction used and result
    with open(path + '/location.txt', 'w') as logfile:
        logfile.write('%s\nPath = %s\nCorrection = %d sec\n%d matched out of %d' %
                      (datetime.now(),
                       path,
                       correction_seconds,
                       photo_count,
                       len(photos)))

    return output_data


def get_exif_data():

    # Build list photos with date taken from exif metadata
    list = []
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            # for ifd_name in exif_dict:
            #     if ifd_name == 'thumbnail':
            #         break
            #     print("\n{0} IFD:".format(ifd_name))
            #     for key in exif_dict[ifd_name]:
            #         try:
            #             print(key, exif_dict[ifd_name][key][:20])
            #         except:
            #             print(key, exif_dict[ifd_name][key])

            photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
            rec = (datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"), os.path.basename(entry.path))
            list.append(rec)
    # Sort list by date/time
    list.sort()
    # for item in list:
    #     print(item)

    # Build csv file with location matching photo time
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            with open(entry.path, 'r') as file:
                gpx_data = file.read()
            csv_data = match_locations(gpx_data, list)
            with open(entry.path.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
                csv_file.write(csv_data)




if __name__ == '__main__':
    get_exif_data()

