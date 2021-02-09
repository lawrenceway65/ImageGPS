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
                for record in photo_data:
                    if record.filename == os.path.basename(entry.path):
                        gps_dict = create_gps_dict(record.latitude, record.longitude, record.elevation)
                        break

                exif_dict.update(gps_dict)
                exif_bytes = piexif.dump(exif_dict)
                jpeg_file = Image.open(entry.path)
                jpeg_file.save(entry.path, "jpeg", exif=exif_bytes)


if __name__ == '__main__':
    get_exif_data()

