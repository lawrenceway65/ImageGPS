import PySimpleGUI as sg
import matchlocations as ml
import re
import os
import gpxpy
import gpxpy.gpx
import webbrowser
from PIL import Image, ImageTk
import calculatecorrection
import updateexif as ue

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
    """Check if GPX file present in selected folder"""
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            return entry.path
    # Not found
    return ''


def get_gpx_data(gpx_file, set_data):
    """Get first and last gpx point and update in set data
    :param gpx_file: gpx filespec
    :param set_data: data to update
    """
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
    """Match locations for the photo in the folder and update the window"""
    ml.match_locations(gpx_filespec, photo_data, path, correction)
    set_data = get_set_data(photo_data)
    sg.popup_ok('Photo Location analysis complete, %d photos checked, %d matched.'
                % (set_data['photo_count'], set_data['matched_count']))

    # Get gpx data
    get_gpx_data(gpx_filespec, set_data)
    gpx_file = os.path.basename(gpx_filespec)

    # Update window info
#    window['-DISPLAY-GPX-'].update(gpx_file)
    window['-PHOTOS-'].update('%d' % set_data['photo_count'])
    window['-MATCHED-'].update('%d' % set_data['matched_count'])
    window['-FIRST_PHOTO-'].update(set_data['first_photo'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-LAST_PHOTO-'].update(set_data['last_photo'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-GPX_START-'].update(set_data['first_gps'].strftime('%d:%m:%Y %H:%M:%S'))
    window['-GPX_END-'].update(set_data['last_gps'].strftime('%d:%m:%Y %H:%M:%S'))

    # Display list of photos
    display_list = []
    for item in photo_data:
        s = '%s   %s   %2.3f %2.3f' % (item.filename,
                                       item.timestamp.strftime('%d:%m:%Y %H:%M:%S'),
                                       item.latitude,
                                       item.longitude)
        display_list.append(s)
    window['-PHOTOLIST-'].update(display_list)
    window['-WRITE_CHANGES-'].update(disabled=False)


def clear_photo_data():
    """Reset all window fields"""
    photo_data.clear()
    correction = 0.0

#    window['-DISPLAY_FOLDER-'].update('')
#    window['-DISPLAY-GPX-'].update('')
    window['-PHOTOS-'].update('')
    window['-MATCHED-'].update('')
    window['-FIRST_PHOTO-'].update('')
    window['-LAST_PHOTO-'].update('')
    window['-GPX_START-'].update('')
    window['-GPX_END-'].update('')
    window['-LAT-'].update('')
    window['-LONG-'].update('')
    window['-CORRECTION-'].update('0')
    window['-PHOTOLIST-'].update(values=[' '])
    window['-THUMBNAIL-'].update(data=None)


# Main window definition
sg.theme('SystemDefault1')
sg.SetOptions(font=('Arial', 12),
              background_color='light gray',
              element_background_color='light gray',
              text_element_background_color='light gray')
layout = [
    [sg.Text('Folder', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Text('folder not selected', size=(34, 1), font=('Arial', 20), text_color='blue', justification='left', key='-DISPLAY_FOLDER-'),
     sg.Input('-', size=(1, 1), enable_events=True, key='-SOURCE_FOLDER-', visible=False), sg.FolderBrowse()],
    [sg.Text('GPX File', size=(15, 1), auto_size_text=False, justification='left'),
     sg.Text('gpx file not selected', size=(60, 1), key='-DISPLAY-GPX-'),
     sg.Input('-', size=(1, 1), enable_events=True, key='-SELECT_GPX_FILE-', visible=False), sg.FileBrowse()],
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
             [sg.Image(size=(275, 275), background_color='dark gray', key='-THUMBNAIL-')],
             [sg.Btn('Write changes', disabled=True, key='-WRITE_CHANGES-')]])
     ],
    [sg.Btn('Exit', key='-EXIT-')]
]
window = sg.Window('Match Locations', layout)

latitude = 0.0
longitude = 0.0

# Main window event loop
while True:
    event, values = window.read()
    print(event)

    if event == '-EXIT-' or event == sg.WINDOW_CLOSED:
        break

    elif event == '-SOURCE_FOLDER-':
        clear_photo_data()
        path = values['-SOURCE_FOLDER-']
        if not path == '':
            # Get folder name from path and update window info
            dir_name = os.path.basename(path)
            window['-DISPLAY_FOLDER-'].update(os.path.basename(path))

            # Is there a gpx file in folder? - if so analyse it
            gpx_filespec = check_gpx(path)
            if not gpx_filespec == '':
                window['-DISPLAY-GPX-'].update(os.path.basename(gpx_filespec))
                ml.load_photo_data(path, photo_data)
                analyse_folder()

    elif event == '-SELECT_GPX_FILE-':
        gpx_filespec = values['-SELECT_GPX_FILE-']
        if not gpx_filespec == '':
            # Get filename from path and update window info
            window['-DISPLAY-GPX-'].update(os.path.basename(gpx_filespec))
            # Has a path already been selected - if so analyse it
            if not path == '':
                clear_photo_data()
                ml.load_photo_data(path, photo_data)
                analyse_folder()

    elif event == '-PHOTOLIST-':
        selected = values['-PHOTOLIST-']
        for item in selected:
            params = re.split(' ', item)
            img_file = params[0]
        for item in photo_data:
            if item.filename == img_file:
                selected_photo = item
                break
        window['-LAT-'].update(selected_photo.latitude)
        window['-LONG-'].update(selected_photo.longitude)
        window['-DISPLAY-'].update(disabled=False)
        window['-CORRECTION-'].update(disabled=False)

        image = Image.open(path + os.sep + selected_photo.filename)
        image.thumbnail((275, 275))
        photo_img = ImageTk.PhotoImage(image)
        window['-THUMBNAIL-'].update(data=photo_img)

    elif event == '-DISPLAY-':
        webbrowser.open_new_tab(selected_photo.get_osm_link())

    elif event == '-CORRECTION-':
        try:
            correction = float(values['-CORRECTION-'])
            window['-APPLY_CORRECTION-'].update(disabled=False)
        except ValueError:
            correction = 0.0

    elif event == '-APPLY_CORRECTION-':
        window['-APPLY_CORRECTION-'].update(disabled=True)
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

    elif event == '-WRITE_CHANGES-':
        if sg.PopupOKCancel('OK to write changes to files?\n This operation is not reversible') == 'OK':
            # Disable button so can't do it twice
            window['-WRITE_CHANGES-'].update(disabled=True)
            # Write the changes
            ue.update_exif(path, gpx_filespec)
            sg.popup_ok('Changes written %d files.' % len(photo_data))

    if latitude == 0.0 and longitude == 0.0:
        window['-CALC_CORRECTION-'].update(disabled=True)
    else:
        window['-CALC_CORRECTION-'].update(disabled=False)

window.close()


