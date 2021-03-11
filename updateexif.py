""" Add a comment """
from PIL import Image
from datetime import datetime
from datetime import timedelta
import os
import re
import piexif
from fractions import Fraction
from photmetadata import PhotoMetadata
import PySimpleGUI as sg
import progressmeter as pm


# EXIF magic numbers from CIPA DC-008-Translation-2012
DateTimeOriginal = 36867
DateTimeDigitized = 36868

# System specific path
if os.name == 'nt':
    path = "D:\\Pictures\\2021\\2021_Test_AddlestoneMorningWalk"
else:
    path = '/Users/lawrence/Pictures/Photos/2021/2021_01_HamptontoKingston'

# Time correction to apply to photo time
# correction_seconds = 0
# correction = timedelta(0, correction_seconds)


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


def update_exif(path, gpx_filespec):
    """Update exif info in files
    :type path: str
    :type gpx_filespec: str
    :return count of photos updated
    """
    photos = []

    # Read in data
    gpx_filename = os.path.basename(gpx_filespec)
    with open(path + os.sep + gpx_filename.replace('.gpx', '') + '_locations.csv', 'r') as csv_file:
        header_line = csv_file.readline()
        for line in csv_file:
            # Create record and add to list if matched
            csv_data = re.split(',', line)
            if float(csv_data[4]) != 0:
                rec = PhotoMetadata(csv_data[0],
                                    datetime.strptime(csv_data[2], "%d:%m:%Y %H:%M:%S"),
                                    float(csv_data[3]),
                                    float(csv_data[4]),)
                photos.append(rec)

    if len(photos) == 0:
        # No valid data so return
        return 0

    photos_updated = 0
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            original_time = exif_dict['Exif'][DateTimeOriginal].decode()

            # Find the photo in the list
            for record in photos:
                if record.filename == os.path.basename(entry.path):
                    pm.ProgressBar('Update files', photos_updated, len(photos), record.filename)
                    photos_updated += 1

                    gps_dict = create_gps_dict(record.latitude, record.longitude, record.elevation)

                    # Write the data
                    update_time = datetime.strftime(record.timestamp_corrected, "%Y:%m:%d %H:%M:%S")
                    exif_dict['Exif'][DateTimeOriginal] = update_time.encode()
                    exif_dict['Exif'][DateTimeDigitized] = update_time.encode()
                    exif_dict.update(gps_dict)
                    exif_bytes = piexif.dump(exif_dict)
                    jpeg_file = Image.open(entry.path)
                    jpeg_file.save(entry.path, "jpeg", exif=exif_bytes)

                    # Output a log - need to record when we do this
                    log = ('%s :%s exif updated. Original: %s New: %s'
                          % (datetime.strftime(datetime.now(), "%Y:%m:%d %H:%M:%S"),
                             os.path.basename(entry.path),
                             original_time,
                             update_time))
                    # print(log)
                    with open('%s/exif_update.log' % path, 'a') as logfile:
                        logfile.write(log + '\n')

                    # Found and updated so no need to search further
                    break

    pm.ProgressBarDelete()

    return photos_updated


if __name__ == '__main__':
    gpx_filespec = ''
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            gpx_filespec = entry.path
            break

    if gpx_filespec != '':
        update_exif(path, gpx_filespec)
