import PySimpleGUI as sg

# For progress meter
window = None


def ProgressBar(window_title, progress, total, filename=''):
    """Custom one line progress meter
    :param window_title: title for progress window
    :param progress: items processed
    :param total: total items
    :param filename: name of last file processed
    """
    global window
    if window is None:
        layout = [[sg.Text('', size=(20,1), key='-COUNT-')],
                  [sg.Text('', size=(20,1), key='-PHOTO-')],
                  [sg.ProgressBar(total, orientation='h', size=(20, 20), border_width=1, relief='RELIEF_SUNKEN', key='-PROGRESS-')]
                  ]

        # create the Window
        window = sg.Window(window_title, layout, modal=True)

    event, values = window.read(timeout=0)
    window['-COUNT-'].update('Photo %d of %d' % (progress, total))
    window['-PHOTO-'].update(filename)
    window['-PROGRESS-'].update_bar(progress)


def ProgressBarDelete():
    global window
    window.close()
    window = None


