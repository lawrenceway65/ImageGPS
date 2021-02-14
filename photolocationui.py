import PySimpleGUI as sg
import matchlocations
from photmetadata import PhotoMetadata

# # All the stuff inside your window.
# layout = [  [sg.Text('Some text on Row 1')],
#             [sg.Text('Enter something on Row 2'), sg.InputText()],
#             [sg.Button('Ok'), sg.Button('Cancel')] ]
#
# # Create the Window
# window = sg.Window('Window Title', layout)
# # Event Loop to process "events" and get the "values" of the inputs
# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
#         break
#     print('You entered ', values[0])
#
# window.close()

sg.theme('SystemDefault1')  # please make your creations colorful

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


# Main window definition
layout = [
    [sg.Text('Folder', size=(15, 1), auto_size_text=False, justification='right'), sg.Text('folder not selected', key='__PHOTO_FOLDER__'), sg.FolderBrowse()],
    [sg.Text('GPX File', size=(15, 1), auto_size_text=False, justification='right'), sg.Text('gpx file not selected', key='__GPX_FILE__'), sg.FileBrowse()],
    [sg.Frame('Data', layout=[[sg.Text('Photos:'), sg.Text('First Photo:'), sg.Text('Last Photo:')],
                              [sg.Text('Matched Photos:'), sg.Text('GPX Start:'), sg.Text('GPX End:')]])],
    [sg.Btn('Exit', key='__EXIT__')]
]
window = sg.Window('Match Locations', layout)
while True:
    event, values = window.read()
    print(event)
#    print(values[0])

    if event == '__EXIT__':
        break

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

