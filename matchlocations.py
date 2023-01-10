""" Add a comment """
from PIL import Image
import gpxpy
import gpxpy.gpx
from datetime import datetime
from datetime import timedelta
import time
import os
import piexif
from photmetadata import PhotoMetadata
import PySimpleGUI as sg
from progressmeter import ProgressBar


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
hardcoded_correction = timedelta(0, correction_seconds)

osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'


def match_locations(gpx_filespec, photo_data, path, correction_seconds=0):
    """For each photo record, find the co-ordinates for the matching time from the gpx data
    If a correction is set apply it to the photo time (for when camera time was set wrong).
    :param gpx_xml: gpx data
    :type gpx_xml: xml
    :type photo_data: PhotoMetadata[]
    :type path: str
    :type correction: float
    """
    # Variables
    photo_count = 0
    correction = timedelta(0, correction_seconds)

    progress_bar = ProgressBar('Match Locations', len(photo_data))

    # Reset data
    for item in photo_data:
        item.timestamp_corrected = item.timestamp_original
        item.reset_gps()

    with open(gpx_filespec, 'r') as file:
        gpx_data = file.read()
    input_gpx = gpxpy.parse(gpx_data)

    # Ignore photos before start of track
    for track in input_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_time = time.localtime(point.time.timestamp())
                # Apply correction
                photo_data[photo_count].timestamp_corrected = photo_data[photo_count].timestamp_original + correction
                photo_time = time.localtime(photo_data[photo_count].timestamp_corrected.timestamp())
                # Find first photo after start of gpx track
                while point_time > photo_time:
                    photo_count += 1
                    progress_bar.Update(photo_count)
                    if photo_count < len(photo_data):
                        photo_data[photo_count].timestamp_corrected = photo_data[photo_count].timestamp_original + correction
                        photo_time = time.localtime(photo_data[photo_count].timestamp_corrected.timestamp())
                    else:
                        break
                break

    # Parse to gpx and iterate through remaining photos, if there are any
    if photo_count < len(photo_data):
        for track in input_gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    point_time = time.localtime(point.time.timestamp())
                    # Apply correction
                    photo_data[photo_count].timestamp_corrected = photo_data[photo_count].timestamp_original + correction
                    photo_time = time.localtime(photo_data[photo_count].timestamp_corrected.timestamp())
                    # May be many photos at one point
                    while point_time > photo_time and photo_count < len(photo_data):
                        # Found a match so update
                        photo_data[photo_count].set_gps(point.latitude, point.longitude, point.elevation)
                        # Next one
                        photo_count += 1
                        progress_bar.Update(photo_count)
                        if photo_count >= len(photo_data):
                            break
                        photo_data[photo_count].timestamp_corrected = photo_data[photo_count].timestamp_original + correction
                        photo_time = time.localtime(photo_data[photo_count].timestamp_corrected.timestamp())

                    if photo_count >= len(photo_data):
                        break

    print('%s matched out of %s' % (photo_count, len(photo_data)))

    progress_bar.Delete()


def get_photo_data(path, photo_data, gpx_file=''):
    """Build list photos with date taken from exif metadata
    Match photos to gpx track based on time and build list
    :type path: str
    :type photo_data: list of PhotoMetaData
    :type gpx_file: path to gpx file
    """
    # Build list of photos
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            # Only photos without GPS data already
            if not exif_dict['GPS']:
                photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
                rec = PhotoMetadata(os.path.basename(entry.path), datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"))
                photo_data.append(rec)
    # Sort list by date/time
    photo_data.sort()

    # If file not passed in open now.
    if gpx_file == '':
        for entry in os.scandir(path):
            if (entry.path.endswith(".gpx")):
                gpx_file = entry.path

    with open(gpx_file, 'r') as file:
        gpx_data = file.read()

    # Match photo location matching photo time and write results to csv
    match_locations(gpx_data, photo_data, path)
    with open(entry.path.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
        csv_file.write('Photo,Date/Time,Lat,Long,Link,Location\n')
        for record in photo_data:
            csv_file.write(record.csv_output())

    return len(photo_data)


def load_photo_data(path, photo_data, load_image_with_gps=False):
    """Build list photos with date taken from exif metadata
    :type path: str
    :type photo_data: list of PhotoMetaData
    :param load_image_with_gps: flag if files that already have gps info are loaded
    """
    # Build list of photos
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            # Only photos without GPS data already
            if not exif_dict['GPS'] or load_image_with_gps:
                photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
                rec = PhotoMetadata(os.path.basename(entry.path), datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"))
                photo_data.append(rec)
    # Sort list by date/time
    photo_data.sort()

    return


if __name__ == '__main__':
    photo_data = []
    get_photo_data(hardcoded_path, photo_data)

