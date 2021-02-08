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
from fractions import Fraction


# EXIF magic numbers from CIPA DC-008-Translation-2012
DateTimeOriginal = 36867
DateTimeDigitized = 36868

# System specific path
if os.name == 'nt':
    path = "D:\\Pictures\\2021\\2021_Test_AddlestoneMorningWalk"
else:
    path = '/Users/lawrence/Pictures/Photos/2021/2021_Test_AddlestoneMorningWalk'

# Time correction to apply to photo time
correction_seconds = 48
correction = timedelta(0, correction_seconds)

# Controls if metadata should be updated
update_exif = True

# path = '/Users/lawrence/Pictures/Photos/2021/2021_03_AddlestoneWalk'
osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'

""" Next three functions from 
https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72#file-exif-py
with minor modes
"""
def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def create_gps_dict(lat, long, elevation):
    """Create GPS dictionary item as EXIF metadata
    Keyword arguments:
    :type lat: float
    :type long: float
    :type elevation: float
    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(long, ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSAltitudeRef: 1,
        piexif.GPSIFD.GPSAltitude: change_to_rational(round(elevation)),
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
    }

    exif_dict = {"GPS": gps_ifd}

    return exif_dict
# End of extract from https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72#file-exif-py


def get_locality(latitude, longitude):
    """Get location from co-ordinates, using Open Street Map.
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
                                                   # 'osm_link',
                                                   # 'get_locality(point.latitude, point.longitude)')
                                                   osm_link,
                                                   get_locality(point.latitude, point.longitude))
                    print(s)
                    output_data += s
                    output_data += '\n'

                    # Update lat long
                    photos[photo_count][2] = point.latitude
                    photos[photo_count][3] = point.longitude
                    photos[photo_count][4] = point.elevation

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
            photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
            rec = [datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"), os.path.basename(entry.path), 0.0, 0.0, 0.0]
            list.append(rec)
    # Sort list by date/time
    list.sort()

    # Build csv file with location matching photo time
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            with open(entry.path, 'r') as file:
                gpx_data = file.read()
            csv_data = match_locations(gpx_data, list)
            with open(entry.path.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
                csv_file.write(csv_data)

    # for item in list:
    #     print(item)

    # If required, make the correction
    if update_exif:
        for entry in os.scandir(path):
            if (entry.path.endswith(".jpg")):
                exif_dict = piexif.load(entry.path)
                corrected_original_time = datetime.strptime(exif_dict['Exif'][DateTimeOriginal].decode(), "%Y:%m:%d %H:%M:%S") + correction
                corrected_digitization_time = datetime.strptime(exif_dict['Exif'][DateTimeDigitized].decode(), "%Y:%m:%d %H:%M:%S") + correction
                # Output a log - need to record when we do this
                print('Old: %s; New: %s; Correction: %d'
                      % (datetime.strptime(exif_dict['Exif'][DateTimeOriginal].decode(), "%Y:%m:%d %H:%M:%S"),
                         corrected_original_time,
                         correction_seconds))

                # Write the data
                exif_dict['Exif'][DateTimeOriginal] = corrected_original_time.strftime("%Y:%m:%d %H:%M:%S").encode()
                exif_dict['Exif'][DateTimeDigitized] = corrected_digitization_time.strftime("%Y:%m:%d %H:%M:%S").encode()

                # Find the photo in the list
                for record in list:
                    if record[1] == os.path.basename(entry.path):
                        gps_dict = create_gps_dict(record[2], record[3], record[4])
                        break

                exif_dict.update(gps_dict)
                exif_bytes = piexif.dump(exif_dict)
                jpeg_file = Image.open(entry.path)
                jpeg_file.save(entry.path, "jpeg", exif=exif_bytes)


if __name__ == '__main__':
    get_exif_data()

