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

window = None


def ProgressBar(progress, total, filename=''):
    """Custom one line progress meter
    :param progress: items processed
    :param total: total items
    :param filename: name of last file processed
    """
    global window
    if window is None:
        layout = [[sg.Text('Matching...')],
                  [sg.Text('', size=(20,1), key='-COUNT-')],
                  [sg.Text('', size=(20,1), key='-PHOTO-')],
                  [sg.ProgressBar(total, orientation='h', size=(20, 20), border_width=1, relief='RELIEF_SUNKEN', key='-PROGRESS-')]
                  ]

        # create the Window
        window = sg.Window('Matching Locations', layout, modal=True)

    event, values = window.read(timeout=0)
    window['-COUNT-'].update('Photo %d of %d' % (progress, total))
    window['-PHOTO-'].update(filename)
    window['-PROGRESS-'].update_bar(progress)


def ProgressBarDelete():
    global window
    window.close()
    window = None


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

    with open(gpx_filespec, 'r') as file:
        gpx_data = file.read()

    # Parse to gpx and iterate through
    input_gpx = gpxpy.parse(gpx_data)
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

    gpx_filename = os.path.basename(gpx_filespec)
    with open(path + os.sep + gpx_filename.replace('.gpx', '') + '_locations.csv', 'w') as csv_file:
        csv_file.write('Photo,Date/Time,Lat,Long,Link,Location\n')
        i = 0
        for record in photo_data:
            ProgressBar(i, len(photo_data), record.filename)
            i += 1
            csv_file.write(record.csv_output())
        ProgressBarDelete()


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


def load_photo_data(path, photo_data):
    """Build list photos with date taken from exif metadata
    :type path: str
    :type photo_data: list of PhotoMetaData
    """
    # Build list of photos
    for entry in os.scandir(path):
        if (entry.path.endswith(".jpg")):
            exif_dict = piexif.load(entry.path)
            photo_datetime = exif_dict['Exif'][DateTimeOriginal].decode()
            rec = PhotoMetadata(os.path.basename(entry.path), datetime.strptime(photo_datetime, "%Y:%m:%d %H:%M:%S"))
            photo_data.append(rec)
    # Sort list by date/time
    photo_data.sort()

    return


if __name__ == '__main__':
    photo_data = []
    get_photo_data(hardcoded_path, photo_data)

