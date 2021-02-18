import PySimpleGUI as sg
import matchlocations
import re
import os
import gpxpy
import gpxpy.gpx
import webbrowser
from PIL import Image, ImageTk
import calculatecorrection

from datetime import datetime
from photmetadata import PhotoMetadata


# Key data is global
# Folder with photos to label
path = ''
# GPX file to use for reference
gpx_filespec = ''
# Data on the set of photos and track
set_data = None
# Data on each photo (list of PhotoMetaData objects)
photo_data = []
# The time correction to apply (seconds)
correction = 0.0


def get_folder():
    """Dialog to get folder to analyse.
    :return str path
    """
    sg.FolderBrowse()

    # layout = [[sg.Text('Photo Location - Select Folder')],
    #         [sg.Input(), sg.FolderBrowse()],
    #         [sg.OK(), sg.Cancel()]]
    #
    # window = sg.Window('Select folder to analyse', layout)
    #
    # event, values = window.read()
    # window.close()
    # if event == 'OK':
    #     return values[0]
    # else:
    #     return ''


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

    matchlocations.match_locations(gpx_filespec, photo_data, path, correction)
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

    # Display list of photos
    display_list = []
    for item in photo_data:
        s = '%s\t%s\t%2.3f\t%2.3f' % (item.filename,
                                       item.timestamp.strftime('%d:%m:%Y %H:%M:%S'),
                                       item.latitude,
                                       item.longitude)
        display_list.append(s)
    window['-PHOTOLIST-'].update(display_list)

    return


# Main window definition
sg.theme('SystemDefault1')
sg.SetOptions(font=('Arial', 14))
layout = [
    [sg.Text('Folder', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Input('folder not selected', size=(60, 1), enable_events=True, key='-SOURCE_FOLDER-'), sg.FolderBrowse()],
    [sg.Text('GPX File', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Text('gpx file not selected', size=(60, 1), key='-GPX_FILE-'),
     sg.Btn('Select', key='-SELECT_GPX_FILE-')],
    [sg.Frame('Data', layout=[[sg.Text('Photos:', size=(20, 1)), sg.Text('', size=(3, 1), key='-PHOTOS-'),
                               sg.Text('First Photo:', size=(20, 1)), sg.Text('', size=(20, 1), key='-FIRST_PHOTO-'),
                               sg.Text('Last Photo:', size=(20, 1)), sg.Text('', size=(20, 1), key='-LAST_PHOTO-')],
                              [sg.Text('Matched Photos:', size=(20, 1)), sg.Text('', size=(3, 1), key='-MATCHED-'),
                               sg.Text('GPX Start:', size=(20, 1)), sg.Text('', size=(20, 1), key='-GPX_START-'),
                               sg.Text('GPX End:', size=(20, 1)), sg.Text('', size=(20, 1), key='-GPX_END-')]])],
    [sg.Listbox(values=[' '], select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, enable_events=True, size=(75, 20), key='-PHOTOLIST-'),
     sg.Col([[sg.Text('Latitude:', size=(10, 1)), sg.Input('', size=(15, 1), enable_events=True, key='-LAT-')],
             [sg.Text('Longitude:', size=(10, 1)), sg.Input('', size=(15, 1), enable_events=True, key='-LONG-')],
             [sg.Text('Correction:', size=(10, 1)), sg.Input('0', disabled=True, size=(10, 1), enable_events=True, key='-CORRECTION-')],
             [sg.Btn('Display', disabled=True, key='-DISPLAY-'),
              sg.Btn('Calc Correction', disabled=True, key='-CALC_CORRECTION-'),
              sg.Btn('Apply', disabled=True, key='-APPLY_CORRECTION-')],
             [sg.Image(size=(275, 275), background_color='light gray', key='-THUMBNAIL-')]])
     ],
    [sg.Btn('Exit', key='-EXIT-')]
]
window = sg.Window('Match Locations', layout)

latitude = 0.0
longitude = 0.0

while True:
    event, values = window.read()
    print(event)

    if event == '-EXIT-' or event == sg.WINDOW_CLOSED:
        break

    elif event == '-SOURCE_FOLDER-':
        path = values['-SOURCE_FOLDER-']
        if not path == '':
            # Get folder name from path and update window info
            path_list = re.split('/', path)
            dir_name = path_list[len(path_list) - 1]
            window['-SOURCE_FOLDER-'].update(dir_name)

            # Is there a gpx file
            gpx_filespec = check_gpx(path)
            if not gpx_filespec == '':
                # Get filename from path and update window info
                path_list = re.split('/', gpx_filespec)
                gpx_file = path_list[len(path_list) - 1]
                window['-GPX_FILE-'].update(gpx_file)
                photo_data.clear()
                matchlocations.load_photo_data(path, photo_data)
                analyse_folder()

    elif event == '-SELECT_GPX_FILE-':
        gpx_filespec = get_file()
        if not gpx_filespec == '':
            # Get filename from path and update window info
            path_list = re.split('/', gpx_filespec)
            gpx_file = path_list[len(path_list) - 1]
            window['-GPX_FILE-'].update(gpx_file)
            # Has a path already been selected
            if not path == '':
                photo_data.clear()
                matchlocations.load_photo_data(path, photo_data)
                analyse_folder()

    elif event == '-PHOTOLIST-':
        selected = values['-PHOTOLIST-']
        for item in selected:
            params = re.split('\t', item)
            img_file = params[0]
        for item in photo_data:
            if item.filename == img_file:
                selected_photo = item
                break
        window['-LAT-'].update(selected_photo.latitude)
        window['-LONG-'].update(selected_photo.longitude)
        window['-DISPLAY-'].update(disabled=False)
        window['-CORRECTION-'].update(disabled=False)

        image = Image.open(path + '/' + selected_photo.filename)
        image.thumbnail((275, 275))
        photo_img = ImageTk.PhotoImage(image)
        window['-THUMBNAIL-'].update(data=photo_img)

    elif event == '-DISPLAY-':
        webbrowser.open_new_tab(selected_photo.get_osm_link())

    elif event == '-CORRECTION-':
        try:
            correction = float(values['-CORRECTION-'])
            window['-APPLY_CORRECTION-'].update(disabled=False)
#            print(correction)
        except ValueError:
            correction = 0.0

    elif event == '-APPLY_CORRECTION-':
        analyse_folder()

    elif event == '-CALC_CORRECTION-':
        correction = calculatecorrection.calculate_correction(path, selected_photo.filename, gpx_filespec, latitude, longitude)
        window['-CORRECTION-'].update(correction)
        if not correction == 0.0:
            window['-APPLY_CORRECTION-'].update(disabled=False)
        # Can reset now
        latitude = longitude = 0.0

    elif event == '-LAT-':
        try:
            latitude = float(values['-LAT-'])
        except ValueError:
            latitude = 0.0

    elif event == '-LONG-':
        try:
            longitude = float(values['-LONG-'])
        except ValueError:
            longitude = 0.0

    if latitude == 0.0 and longitude == 0.0:
        window['-CALC_CORRECTION-'].update(disabled=True)
    else:
        window['-CALC_CORRECTION-'].update(disabled=False)



window.close()


