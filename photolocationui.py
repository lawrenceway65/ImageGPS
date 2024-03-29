import PySimpleGUI as sg
import matchlocations as ml
import os
import gpxpy
import gpxpy.gpx
import webbrowser
from PIL import Image, ImageTk
import calculatecorrection
import updateexif2 as ue
import time


# Key data is global
# Folder with photos to label
path = ''
# GPX file to use for reference
gpx_filespec = ''
# Data on the set of photos and track
# set_data = None
# Data on each photo (list of PhotoMetaData objects)
photo_data = []
# The time correction to apply (seconds)
correction = 0.0


class PhotoSetData:
    """Hold data relating to set of photos"""
    def __init__(self, photo_data):
        self.matched_photos_count = 0
        for item in photo_data:
            if item.point_found:
                self.matched_photos_count += 1

        self.first_photo = time.localtime(photo_data[0].timestamp_corrected.timestamp())
        self.last_photo = time.localtime(photo_data[len(photo_data)-1].timestamp_corrected.timestamp())
        self.photo_count = len(photo_data)
        self.first_gps = None
        self.last_gps = None

    def set_gpx_data(self, gpx_file):
        """Get first and last gpx point and update in set data
        :param gpx_file: gpx filespec
        """
        with open(gpx_file, 'r') as file:
            gpx_data = file.read()
            input_gpx = gpxpy.parse(gpx_data)
            for track in input_gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if self.first_gps is None:
                            # Set first point
                            self.first_gps = time.localtime(point.time.timestamp())
                # Set last point
                self.last_gps = time.localtime(point.time.timestamp())


def check_gpx(path):
    """Check if GPX file present in selected folder"""
    for entry in os.scandir(path):
        if (entry.path.endswith(".gpx")):
            return entry.path
    # Not found
    return ''


def analyse_folder(selected_index=0):
    """Match locations for the photo in the folder and update the window"""
    ml.match_locations(gpx_filespec, photo_data, path, correction)
    set_data = PhotoSetData(photo_data)

    # Get gpx data
    set_data.set_gpx_data(gpx_filespec)

    # Update window info
    window['-PHOTOS-'].update('%d' % set_data.photo_count)
    window['-MATCHED-'].update('%d' % set_data.matched_photos_count)
    window['-FIRST_PHOTO-'].update(time.strftime('%d:%m:%Y %H:%M:%S', set_data.first_photo))
    window['-LAST_PHOTO-'].update(time.strftime('%d:%m:%Y %H:%M:%S', set_data.last_photo))
    window['-GPX_START-'].update(time.strftime('%d:%m:%Y %H:%M:%S', set_data.first_gps))
    window['-GPX_END-'].update(time.strftime('%d:%m:%Y %H:%M:%S', set_data.last_gps))

    # Set colours according to match
    if set_data.first_photo < set_data.first_gps:
        window['-FIRST_PHOTO-'].update(text_color='red')
    else:
        window['-FIRST_PHOTO-'].update(text_color='green')

    if set_data.last_photo > set_data.last_gps:
        window['-LAST_PHOTO-'].update(text_color='red')
    else:
        window['-LAST_PHOTO-'].update(text_color='green')

    if set_data.photo_count == set_data.matched_photos_count:
        window['-MATCHED-'].update(text_color='green')
    else:
        window['-MATCHED-'].update(text_color='red')

    if set_data.matched_photos_count == 0:
        window['-FIRST_PHOTO-'].update(text_color='red')
        window['-LAST_PHOTO-'].update(text_color='red')

    # Display list of photos
    display_list = []
    for item in photo_data:
        s = '  %s    %s    %2.3f    %2.3f' % (item.filename,
                                              item.timestamp_corrected.strftime('%d:%m:%Y %H:%M:%S'),
                                              item.latitude,
                                              item.longitude)
        display_list.append(s)
    window['-PHOTOLIST-'].update(display_list)
    window['-PHOTOLIST-'].update(set_to_index=selected_index)
    window['-WRITE_CHANGES-'].update(disabled=False)
#    window['-CORRECTION-'].update(disabled=False)
    window['-PLUS1HOUR-'].update(disabled=False)
    window['-MINUS1HOUR-'].update(disabled=False)
    window['-PLUS1MIN-'].update(disabled=False)
    window['-MINUS1MIN-'].update(disabled=False)
    window['-PLUS15SEC-'].update(disabled=False)
    window['-MINUS15SEC-'].update(disabled=False)


def clear_photo_data():
    """Reset all window fields"""
    photo_data.clear()
    global correction, selected_index
    correction = 0.0
    selected_index = 0

    window['-PHOTOS-'].update('')
    window['-MATCHED-'].update('')
    window['-FIRST_PHOTO-'].update('')
    window['-LAST_PHOTO-'].update('')
    window['-GPX_START-'].update('')
    window['-GPX_END-'].update('')
    window['-LAT-'].update('')
    window['-LONG-'].update('')
#    window['-CORRECTION-'].update('0')
    window['-PHOTOLIST-'].update(values=[' '])
    window['-THUMBNAIL-'].update(data=None)
    window['-PLUS1HOUR-'].update(disabled=True)
    window['-MINUS1HOUR-'].update(disabled=True)
    window['-PLUS1MIN-'].update(disabled=True)
    window['-MINUS1MIN-'].update(disabled=True)
    window['-PLUS15SEC-'].update(disabled=True)
    window['-MINUS15SEC-'].update(disabled=True)


# Main window definition
sg.theme('SystemDefault1')
sg.SetOptions(font=('Arial', 12),
              background_color='light gray',
              element_background_color='light gray',
              text_element_background_color='light gray')
layout = [
    [sg.Col([
        [sg.Text('Photo Folder:', size=(12, 1), auto_size_text=False, justification='left'),
        sg.Text('folder not selected', size=(25, 1), font=('Arial', 20), text_color='blue', justification='left', key='-DISPLAY_FOLDER-')],
        [sg.Text('GPX File:', size=(12, 1), auto_size_text=False, justification='left'),
        sg.Text('file not selected', size=(40, 1), key='-DISPLAY-GPX-')]]),
    sg.Col([
        [sg.Input('-', justification='left', size=(1, 1), enable_events=True, key='-SOURCE_FOLDER-', visible=False),
        sg.FolderBrowse('Select Folder', size=(12, 1))],
        [sg.Input('-', justification='left', size=(1, 1), enable_events=True, key='-SELECT_GPX_FILE-', visible=False),
        sg.FileBrowse('Select File', size=(12, 1))]]),
    sg.Col([[sg.Button('Match', size=(6, 2), disabled=True, key='-MATCH-')]])],
    [sg.Frame('Data', layout=[[sg.Text('Photos:', size=(15, 1)), sg.Text('', size=(3, 1), key='-PHOTOS-'),
                               sg.Text('GPX Start:', size=(15, 1)), sg.Text('', size=(15, 1), key='-GPX_START-'),
                               sg.Text('GPX End:', size=(15, 1)), sg.Text('', size=(15, 1), key='-GPX_END-')],
                              [sg.Text('Matched Photos:', size=(15, 1)), sg.Text('', size=(3, 1), key='-MATCHED-'),
                               sg.Text('First Photo:', size=(15, 1)), sg.Text('', size=(15, 1), key='-FIRST_PHOTO-'),
                               sg.Text('Last Photo:', size=(15, 1)), sg.Text('', size=(15, 1), key='-LAST_PHOTO-')]])],
    [sg.Listbox(values=[' '], select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, enable_events=True, size=(55, 25), key='-PHOTOLIST-'),
     sg.Col([[sg.Text('Latitude:', size=(10, 1)), sg.Input('', size=(15, 1), enable_events=True, key='-LAT-')],
             [sg.Text('Longitude:', size=(10, 1)), sg.Input('', size=(15, 1), enable_events=True, key='-LONG-')],
             [sg.Text('Correction:', size=(10, 1)), sg.Input('0', disabled=True, size=(7, 1), enable_events=True, key='-CORRECTION-')],
             [sg.Btn('-1hr', disabled=True, key='-MINUS1HOUR-'),
             sg.Btn('-1mn', disabled=True, key='-MINUS1MIN-'),
             sg.Btn('-15s', disabled=True, key='-MINUS15SEC-'),
             sg.Btn('+15s', disabled=True, key='-PLUS15SEC-'),
             sg.Btn('+1mn', disabled=True, key='-PLUS1MIN-'),
             sg.Btn('+1hr', disabled=True, key='-PLUS1HOUR-')],
             [sg.Btn('Display', disabled=True, key='-DISPLAY-'),
              sg.Btn('Calc Correction', disabled=True, key='-CALC_CORRECTION-'),
              sg.Btn('Apply', disabled=True, key='-APPLY_CORRECTION-')],
             [sg.Image(size=(275, 275), background_color='dark gray', key='-THUMBNAIL-')],
             [sg.Btn('Write changes', disabled=True, key='-WRITE_CHANGES-')]])
     ],
    [sg.Btn('Exit', key='-EXIT-')]
]
window = sg.Window('Find Photo Locations', layout)

latitude = 0.0
longitude = 0.0
selected_index = 0

# Main window event loop
while True:
    event, values = window.read()
    print(event)

    if event == '-EXIT-' or event == sg.WINDOW_CLOSED:
        break

    elif event == '-SOURCE_FOLDER-':
        path = values['-SOURCE_FOLDER-']
        if not path == '':
            # Get folder name from path and update window info
            window['-DISPLAY_FOLDER-'].update(os.path.basename(path))
            clear_photo_data()

            # Is there a gpx file in folder? - if so analyse it
            gpx_filespec = check_gpx(path)
            if gpx_filespec == '':
                window['-DISPLAY-GPX-'].update('file not selected')
            else:
                window['-DISPLAY-GPX-'].update(os.path.basename(gpx_filespec))
                window['-MATCH-'].update(disabled=False)

    elif event == '-MATCH-':
        clear_photo_data()
        ml.load_photo_data(path, photo_data, True)
        if len(photo_data) > 0:
            analyse_folder()
            selected_photo = photo_data[selected_index]
            window['-LAT-'].update(selected_photo.latitude)
            window['-LONG-'].update(selected_photo.longitude)
            with Image.open(path + os.sep + selected_photo.filename) as image:
                image.thumbnail((275, 275))
                photo_img = ImageTk.PhotoImage(image)
                window['-THUMBNAIL-'].update(data=photo_img)
            # If there are co-ordinates allow display of location map
            if selected_photo.latitude == 0 and selected_photo.longitude == 0:
                window['-DISPLAY-'].update(disabled=True)
            else:
                window['-DISPLAY-'].update(disabled=False)
        else:
            sg.PopupOK('All photos already have gps data')

    elif event == '-SELECT_GPX_FILE-':
        gpx_filespec = values['-SELECT_GPX_FILE-']
        if not gpx_filespec == '':
            # Get filename from path and update window info
            window['-DISPLAY-GPX-'].update(os.path.basename(gpx_filespec))
            # Has a path already been selected - if so analyse it
            if not path == '':
                window['-MATCH-'].update(disabled=False)

    elif event == '-PHOTOLIST-':
        selected = values['-PHOTOLIST-']
        # Only ever one item as it's single select, first token in string is filename
        img_file = selected[0].split()[0]
        selected_index = 0
        for item in photo_data:
            if item.filename == img_file:
                selected_photo = item
                break
            selected_index += 1
        window['-LAT-'].update(selected_photo.latitude)
        window['-LONG-'].update(selected_photo.longitude)
        # If there are co-ordinates allow display of location map
        if selected_photo.latitude == 0 and selected_photo.longitude == 0:
            window['-DISPLAY-'].update(disabled=True)
        else:
            window['-DISPLAY-'].update(disabled=False)

        with Image.open(path + os.sep + selected_photo.filename) as image:
            image.thumbnail((275, 275))
            photo_img = ImageTk.PhotoImage(image)
            window['-THUMBNAIL-'].update(data=photo_img)
        window['-PHOTOLIST-'].update(set_to_index=selected_index)

    elif event == '-DISPLAY-':
        webbrowser.open_new_tab(selected_photo.get_osm_link())

    elif event == '-CORRECTION-':
        try:
            correction = float(values['-CORRECTION-'])
            window['-APPLY_CORRECTION-'].update(disabled=False)
        except ValueError:
            correction = 0.0

    elif event == '-PLUS1HOUR-':
        correction += 3600
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

    elif event == '-MINUS1HOUR-':
        correction -= 3600
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

    elif event == '-PLUS1MIN-':
        correction += 60
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

    elif event == '-MINUS1MIN-':
        correction -= 60
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

    elif event == '-PLUS15SEC-':
        correction += 15
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

    elif event == '-MINUS15SEC-':
        correction -= 15
        window['-CORRECTION-'].update(correction)
        analyse_folder(selected_index)

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
            i = ue.update_exif(path, photo_data, gpx_filespec)
            sg.popup_ok('Changes written to %d files.' % i)

    if latitude == 0.0 and longitude == 0.0:
        window['-CALC_CORRECTION-'].update(disabled=True)
    else:
        window['-CALC_CORRECTION-'].update(disabled=False)

window.close()


