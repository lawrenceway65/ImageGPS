import PySimpleGUI as sg
import matchlocations

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


while True:
    photo_data = []
    path = get_folder()
    if not path == '':
        matchlocations.get_photo_data(path, photo_data)
        sg.popup_ok('Photo Location analysis complete, %d photos checked.' % len(photo_data))

    break

