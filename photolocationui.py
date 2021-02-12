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

layout = [  [sg.Text('Photo Location - Select Folder')],
            [sg.Input(), sg.FolderBrowse()],
            [sg.OK(), sg.Cancel()]]

window = sg.Window('Select folder to analyse', layout)

while True:
    event, values = window.read()
    window.close()
    if event == 'OK':
        path = values[0]
        matchlocations.get_photo_data(path)

    break

