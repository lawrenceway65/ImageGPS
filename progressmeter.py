import PySimpleGUI as sg

# For progress meter

class ProgressBar:

    window = None

    def __init__(self, window_title, total, progress=0, filename=''):
        """Custom one line progress meter
        :param window_title: title for progress window
        :param progress: items processed
        :param total: total items
        :param filename: name of last file processed
        """
        self.total = total

        # create the Window
        layout = [[sg.Text('', size=(20,1), key='-COUNT-')],
                  [sg.Text('', size=(20,1), key='-PHOTO-')],
                  [sg.ProgressBar(total, orientation='h', size=(20, 20), border_width=1, relief='RELIEF_SUNKEN', key='-PROGRESS-')]
                  ]
        self.window = sg.Window(window_title, layout, modal=True)

        event, values = self.window.read(timeout=0)
        self.window['-COUNT-'].update('Photo %d of %d' % (progress, self.total))
#        window['-PHOTO-'].update(filename)
        self.window['-PROGRESS-'].update_bar(progress)

    def Update(self, progress, total=0):

        if total != 0:
            self.total = total
        self.window['-COUNT-'].update('Photo %d of %d' % (progress, self.total))
#        window['-PHOTO-'].update(filename)
        self.window['-PROGRESS-'].update_bar(progress)

    def Delete(self):

        self.window.close()
        self.window = None


