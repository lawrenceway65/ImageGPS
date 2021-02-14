import PySimpleGUI as sg
import matchlocations
import re
import os
import gpxpy
import gpxpy.gpx
from datetime import datetime

from photmetadata import PhotoMetadata


sg.theme('SystemDefault1')

def get_folder():
    layout = [[sg.Text('Photo Location - Select Folder')],
            [sg.Input(), sg.FolderBrowse()],
            [sg.OK(), sg.Cancel()]]

    window = sg.Window('Select folder to analyse', layout)

    event, values = window.read()
    window.close()
    if event == 'OK':
        return values[0]
    else:
        return ''

def get_set_data(photo_data):
    """Get data pertaining to set of photos. Return as dictionary
    :type photo_data: list of PhotoMetaData
    """
    matched_photos_count = 0
    for item in photo_data:
        if item.point_found:
            matched_photos_count += 1

    first_photo = photo_data[0].timestamp
    last_photo = photo_data[len(photo_data)-1].timestamp

    set_data = {'photo_count': len(photo_data),
                'matched_count': matched_photos_count,
                'first_photo': first_photo,
                'last_photo': last_photo,
                'first_gps': 0,
                'last_gps': 0}

    return set_data

def check_gpx(path):
    # Check for GPX file
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            return entry.path
    # Not found
    return ''


def get_gpx_data(gpx_file, set_data):
    """Set first and last gpx point"""
    with open(gpx_file, 'r') as file:
        gpx_data = file.read()
        input_gpx = gpxpy.parse(gpx_data)
        for track in input_gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if set_data['first_gps'] == 0:
                        # Set first point
                        set_data['first_gps'] = point.time
            # Set last point
            set_data['last_gps'] = point.time

    return


# Main window definition
layout = [
    [sg.Text('Folder', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Text('folder not selected', size=(60, 1), key='-SOURCE_FOLDER-'),
     sg.Btn('Select', key='-SELECT_SOURCE_FOLDER-')],
    [sg.Text('GPX File', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Text('gpx file not selected', size=(60, 1), key='-GPX_FILE-'),
     sg.Btn('Select', key='-SELECT_GPX_FILE-')],
    [sg.Frame('Data', layout=[[sg.Text('Photos:', size=(20, 1)), sg.Text('', size=(3, 1), key='-PHOTOS-'),
                               sg.Text('First Photo:', size=(20, 1)), sg.Text('', size=(20, 1), key='-FIRST_PHOTO-'),
                               sg.Text('Last Photo:', size=(20, 1)), sg.Text('', size=(20, 1), key='-LAST_PHOTO-')],
                              [sg.Text('Matched Photos:', size=(20, 1)), sg.Text('', size=(3, 1), key='-MATCHED-'),
                               sg.Text('GPX Start:', size=(20, 1)), sg.Text('', size=(20, 1), key='-GPX_START-'),
                               sg.Text('GPX End:', size=(20, 1)), sg.Text('', size=(20, 1), key='-GPX_END-')]])],
    [sg.Btn('Exit', key='-EXIT-')]
]
window = sg.Window('Match Locations', layout)

# Key params
path = None
photo_data = []

while True:
    event, values = window.read()
    print(event)
#    print(values[0])

    if event == '-EXIT-':
        break

    if event == '-SELECT_SOURCE_FOLDER-':
        path = get_folder()
        if path == '':
            break

        # Remove items from list in case it is second time around
        for item in photo_data:
            del item

        matchlocations.get_photo_data(path, photo_data)
        set_data = get_set_data(photo_data)
        sg.popup_ok('Photo Location analysis complete, %d photos checked, %d matched.' % (set_data['photo_count'], set_data['matched_count']))

        # Get gpx data
        gpx_filespec = check_gpx(path)
        if not gpx_filespec == '':
            get_gpx_data(gpx_filespec, set_data)
            path_list = re.split('/', gpx_filespec)
            gpx_file = path_list[len(path_list)-1]

        # Get folder name from path
        path_list = re.split('/', path)
        dir_name = path_list[len(path_list)-1]

        # Update window info
        window['-SOURCE_FOLDER-'].update(dir_name)
        window['-GPX_FILE-'].update(gpx_file)
        window['-PHOTOS-'].update('%d' % set_data['photo_count'])
        window['-MATCHED-'].update('%d' % set_data['matched_count'])
        window['-FIRST_PHOTO-'].update(set_data['first_photo'].strftime('%d:%m:%Y %H:%M:%S'))
        window['-LAST_PHOTO-'].update(set_data['last_photo'].strftime('%d:%m:%Y %H:%M:%S'))
        window['-GPX_START-'].update(set_data['first_gps'].strftime('%d:%m:%Y %H:%M:%S'))
        window['-GPX_END-'].update(set_data['last_gps'].strftime('%d:%m:%Y %H:%M:%S'))




window.close()

# while True:
#     photo_data = []
#     path = get_folder()
#     if not path == '':
#         matchlocations.get_photo_data(path, photo_data)
#         set_data = get_set_data(photo_data)
#         sg.popup_ok('Photo Location analysis complete, %d photos checked, %d matched.' % (set_data['photo_count'], set_data['matched_count']))
#
#     break

