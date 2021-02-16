import PySimpleGUI as sg
import matchlocations
import re
import os
import gpxpy
import gpxpy.gpx
from datetime import datetime
from photmetadata import PhotoMetadata


# Key data is global
path = ''
gpx_filespec = ''
set_data = None
photo_data = []


def get_folder():
    """Dialog to get folder to analyse.
    :return str path
    """
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


def get_file():
    """Dialog to get gpx file, if not in selected folder.
    :return str file name / path
    """
    layout = [[sg.Text('GPX File - Select File')],
            [sg.Input(), sg.FileBrowse(file_types=(("GPX files","*.gpx")))],
            [sg.OK(), sg.Cancel()]]

    window = sg.Window('Select track file', layout)

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


def analyse_folder():

    # Remove items from list in case it is second time around
    photo_data.clear()

    matchlocations.get_photo_data(path, photo_data, gpx_filespec)
    set_data = get_set_data(photo_data)
    sg.popup_ok('Photo Location analysis complete, %d photos checked, %d matched.' % (
    set_data['photo_count'], set_data['matched_count']))

    # Get gpx data
    get_gpx_data(gpx_filespec, set_data)
    # Get filename from path and update window info
    path_list = re.split('/', gpx_filespec)
    gpx_file = path_list[len(path_list) - 1]
    window['-GPX_FILE-'].update(gpx_file)

    # Update window info
    window['-PHOTOS-'].update('%d' % set_data['photo_count'])
    window['-MATCHED-'].update('%d' % set_data['matched_count'])
    window['-FIRST_PHOTO-'].update(set_data['first_photo'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-LAST_PHOTO-'].update(set_data['last_photo'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-GPX_START-'].update(set_data['first_gps'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-GPX_END-'].update(set_data['last_gps'].strftime('%d:%m:%Y %H:%M:%S'))

    return


# Main window definition
sg.theme('SystemDefault1')
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


while True:
    event, values = window.read()
    print(event)

    if event == '-EXIT-' or event == sg.WINDOW_CLOSED:
        break

    if event == '-SELECT_SOURCE_FOLDER-':
        path = get_folder()
        if not path == '':
            # Get folder name from path and update window info
            path_list = re.split('/', path)
            dir_name = path_list[len(path_list) - 1]
            window['-SOURCE_FOLDER-'].update(dir_name)

            # Is there a gpx file
            gpx_filespec = check_gpx(path)
            if not gpx_filespec == '':
                analyse_folder()

    if event == '-SELECT_GPX_FILE-':
        gpx_filespec = get_file()
        if not gpx_filespec == '':
            # Get filename from path and update iwndow info
            path_list = re.split('/', gpx_filespec)
            gpx_file = path_list[len(path_list) - 1]
            window['-GPX_FILE-'].update(gpx_file)
            # Has a path already been selected
            if not path == '':
                analyse_folder()

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

