import tkinter
import tkinter.font as tkFont

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from get_files_with_extension import get_files_with_extension, get_files_without_extension
from load_images_from_dicom import get_list_of_images_from_dicom_file
import pandas as pd
from functools import partial
import numpy as np

class LabelGUI:
    def __init__(
            self, master,
            first_video: int,
            dicom_data_path: str,
            file_extension: str = ""
    ):
        """LabelGUI class generates a GUI to allow assessment of images
        # Arguments:
            first_video (int): integer that indicates at which video file the process should start.
            dicom_data_path (str): main path where the DICOM files are stored
            file_extension (str): extension of the DICOM files containing the images.
        """
        # self.label_mode = 'multiple'


        # Initialize some stuff
        self.labels = []
        self.labelling_buttons = []
        self.frame_num = 0 # start at the first frame of the US sequence
        self.master = master
        self.video_number = first_video
        self.dicom_data_path = dicom_data_path
        self.video_info = pd.DataFrame(columns=['video file', 'scan location'])
        self.frame_info = pd.DataFrame(columns=['video file', 'pathology label'])
        self.frame_index_start = 0  # The index at which the current video is starting in self.frame_info
        self.us_scan_positions = ('RANT', 'LANT', 'LPL',  'RPL', 'LPU', 'RPU')
        self.pathology_labels = ['Normal', 'Collapse', 'Consolidation', 'APO / Int. Syndrome', 'Pneumothorax', 'Effusion', 'B-lines', 'Pleural thickening', 'Irregular pleura']
        self.label_mode = tkinter.StringVar()  # StringVar needed for radio buttons
        self.label_mode.set('multiple')  # TODO The label mode cannot be change to single when labels are already selected in the multiple label mode

        # Defaults for the GUI layout
        self.figure = plt.figure(figsize=np.array((9.6, 7.2))*1.1)  # Resolution of the images we are using is 960x720, this should be done dynamically based on the image input size
        self.figure.set_tight_layout(True)
        self.buttonwidth = 20  # Fits the currently used text for the buttons

        self.create_output_filename()

        # Getting and storing DICOM file names
        self.dicom_file_names = get_files_without_extension(self.dicom_data_path)  # Dicom files often have no extension
        self.dicom_file_names.extend(get_files_with_extension(self.dicom_data_path, 'dcm'))  # Files with Dicom extension .dcm
        print(self.dicom_file_names)
        self.video_info.loc[:, 'video file'] = self.dicom_file_names

        self.init_GUI()

    def create_output_filename(self):
        """ Creates an unique name for the output files such that they are not overwritten
        TODO refactor this function to a generic one and remove it from the class
        :return:
        """
        suffix = os.path.split(self.dicom_data_path)[-1]  # Use the selected folder as a suffix for the filename
        self.frame_output_file = 'frame_info_' + suffix + '.csv'
        self.video_output_file = 'video_info_' + suffix + '.csv'
        self.frame_output_file = self.check_for_duplicate_filename(self.dicom_data_path, self.frame_output_file)
        self.video_output_file = self.check_for_duplicate_filename(self.dicom_data_path, self.video_output_file)

    def check_for_duplicate_filename(self, datapath, filename):
        """ Adds a number to the filename if it already exists

        TODO Bug: For 10 or more files this functions adds an additional _ to the filename
        TODO refactor this function to a generic one and remove it from the class
        :param datapath: (string) The datapath to check for a duplicate name
        :param filename: (string) The filename that is checked for uniqueness
        :return:
        """
        if os.path.exists(os.path.join(datapath, filename)):
            filename = filename[:-4] + '_1' + filename[-4:]  # the last four characters are an extension

        i = 2
        while os.path.exists(os.path.join(datapath, filename)):
            filename = filename[:-6] + '_' + str(i) + filename[-4:] # The index changes when the filename already has been altered
            i += 1
        return filename

    def init_GUI(self) -> None:
        """Create GUI canvas and standard buttons and go to the initial view (scanning position question)
        TODO Make the starting view configurable (it is also hard coded in init_for_next_us_sequence)
        """

        self.figure.clf()

        # Create plotting canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=50, columnspan=3)
        self.init_data_for_us_sequence()
        self.plot_frame()

        self.add_standard_buttons()
        self.label_text_font = tkFont.Font(family='Segoe UI', size=12)
        self.label_text_font_bold = tkFont.Font(family='Segoe UI', size=12, weight='bold')
        self.label_text = tkinter.Label(master=self.master, text='', font=self.label_text_font, bg='white')  # Initialize text label below the figure without text
        self.label_text.grid(row=51)
        self.label_text2 = tkinter.Label(master=self.master, text='', font=self.label_text_font, bg='white')  # Initialize text label below the figure without text

        self.scan_pos_question_components = self.go_to_scan_position_question()  # Start with confirming the scanning position

    def init_data_for_us_sequence(self):
        """ Set the necessary variable when loading a new us sequence

        :return:
        """
        self.frames = get_list_of_images_from_dicom_file(self.dicom_file_names[self.video_number])
        self.frame_index_start = self.frame_info.shape[0]  # The start of the index is the current size of the frame_info DataFrame
        self.frame_index = self.generate_frame_index(self.frame_index_start, len(self.frames))  # the number of indexes is equal to the amount of frames
        frame_index_df = pd.DataFrame(columns=['video file'], data=[self.dicom_file_names[self.video_number]] * len(self.frames))  # create dataframe with the video name for frame_info
        self.frame_info = self.frame_info.append(frame_index_df).fillna('')  # fill all other columns than video_file with an empty string
        self.frame_info.reset_index(drop=True, inplace=True)
        self.frame_num = 0  # Start at the first frame of the sequence

    def show_loading_text(self):
        """ Show text when a new US sequence is loaded

        :return:
        """
        self.loading_text_font_bold = tkFont.Font(family='Segoe UI', size=18, weight='bold')
        self.loading_text = tkinter.Label(master=self.master, text='Loading Data. Please wait.', font=self.loading_text_font_bold, bg='white')
        self.loading_text.grid(row=25, column=1)
        self.master.update_idletasks()  # Needed to display the text immediately

    def remove_loading_text(self):
        """ Remove the loading text completely

        :return:
        """
        self.loading_text.destroy()

    def init_for_next_us_sequence(self):
        """ Go back to the initial view of the GUI for the next us sequence

        :return:
        """
        self.init_data_for_us_sequence()
        self.destroy_list_of_GUI_components(self.labelling_buttons)  # Destroy the existing GUI components (in this case the components in the labelling view)
        self.scan_pos_question_components = self.go_to_scan_position_question()

    def generate_frame_index(self, current, no_frames):
        """ Creates a new index range

        :param current: (int) start of the range
        :param no_frames: (int) the length of the range
        :return:
        """
        return range(current, current + no_frames)

    def plot_frame(self):
        """ Plot a frame of the us sequence onto the GUI canvas

        :return:
        """
        plt.gca()
        plt.imshow(self.frames[self.frame_num], aspect='equal')  # Assumption of square pixels
        plt.xticks([])  # No ticks needed for an image
        plt.yticks([])  # No ticks needed for an image
        plt.title('Frame {} / {}'.format(self.frame_num + 1, len(self.frames)))
        self.canvas.draw()  # Needed to update the display

    def update_frame(self):
        """ Updates the GUI canvas with a new frame

        :return:
        """
        self.figure.axes[0].images[0].set_array(self.frames[self.frame_num])  # Update the data of the figure for speed
        plt.title('Frame {} / {}'.format(self.frame_num + 1, len(self.frames)))
        self.canvas.draw()  # Needed to update the display

    def add_standard_buttons(self):
        """ Add buttons that are used in every view of the GUI

        :return:
        """

        # Create a placeholder for the standard buttons
        std_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        std_button_frame.grid(column=4, row=43)
        std_button_frame.rowconfigure(0, pad=5)
        std_button_frame.rowconfigure(1, pad=5)
        std_button_frame.rowconfigure(2, pad=5)

        # Next and previous frame buttons
        next_frame_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Next Frame (l)",
                                       command=lambda: self.next_frame())
        previous_frame_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Previous Frame (k)",
                                       command=lambda: self.previous_frame())
        next_frame_button.grid(row=0, column=4)
        previous_frame_button.grid(row=1, column=4)

        # Create save button
        save_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Save",
                                     command=lambda: self.save_data())
        save_button.grid(row=2, column=4)

        # Label mode selection radio buttons
        label_mode_frame = tkinter.Frame(self.master, background='white')
        label_mode_frame.grid(column=4, row=5, padx=10, sticky='w')
        label_mode_text = tkinter.Label(master=label_mode_frame, text='Label mode', background='white')
        label_mode_text.grid(sticky='w')

        single_label_rad_button = tkinter.Radiobutton(master=label_mode_frame, text='Single', variable=self.label_mode, value='single',
                                                      bg='white')
        single_label_rad_button.grid(sticky='w')

        multiple_labels_rad_button = tkinter.Radiobutton(master=label_mode_frame, text='Multiple', variable=self.label_mode, value='multiple',
                                                         bg='white')
        multiple_labels_rad_button.grid(sticky='w')

    def next_frame(self):
        """ Goes to the next frame in the us sequence. Also takes care of saving the labels in multiple label mode and
        colors the buttons according to previously chosen labels for a frame.

        :return:
        """
        if self.label_mode.get() == 'multiple':
            if len(self.labels) > 0:
                multiple_label_text = ', '.join(self.labels)  # Create a string
                # The label text is printed in process_label_button_press for the single label mode
                self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label'] = multiple_label_text
                self.print_labelling_text(multiple_label_text)

        if self.frame_num < (len(self.frames)-1):  # Go to the next frame if it is not the last one of the us sequence
            self.restore_color_of_label_buttons()
            self.frame_num += 1
            self.update_labels_attribute()  # To color buttons according to labels that were already done
            for pathology in self.labels:
                self.highlight_label_button(pathology)
            self.update_frame()
        else:
            self.go_to_next_us_sequence()  # Go to the next us sequence if it is the last frame of the us sequence

    def previous_frame(self):
        """ Go to the previous frame in the video and color the label buttons accordingly
        # TODO Support going back to the last frame of the previous video

        :return:
        """
        if self.frame_num > 0:
            self.restore_color_of_label_buttons()  # Go back to the default button color
            self.frame_num -= 1
            self.update_labels_attribute()
            for pathology in self.labels:  # Highlights the buttons of labels added to the frame previously
                self.highlight_label_button(pathology)
            self.update_frame()

    def update_labels_attribute(self):
        """ Set the labels attribute according to the currently displayed frame

        :return:
        """
        pathology_labels = self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label']

        if len(pathology_labels) == 0:
            self.labels = []
        else:
            # Convert the string fromthe frame_info DataFrame back to a list
            pathology_labels = pathology_labels.replace(' ', '', 1)
            self.labels = pathology_labels.split(',')

    def go_to_next_us_sequence(self):
        """ Loads the next video or exits the GUI after the last video

        :return:
        """
        self.save_data() # To not lose data after a complete video has been labelled
        if self.video_number == len(self.dicom_file_names)-1:
            self.done()  # prepare to exit the program
        else:
            self.video_number += 1
            self.show_loading_text()
            self.init_for_next_us_sequence()
            self.remove_loading_text()
            self.update_frame()

    def go_to_scan_position_question(self):
        """ Go to the GUI view to confirm the scanning location

        :return:
        """

        # Create a frame as placeholder
        ques_frame = tkinter.Frame(self.master, padx=10, background='white')
        ques_frame.grid(column=4, row=8)
        ques_frame.rowconfigure(0, pad=5)
        ques_frame.rowconfigure(1, pad=5)
        ques_frame.rowconfigure(2, pad=5)

        # Create scanning location yes / no buttons
        yes_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="Yes",
                                        command=lambda: self.confirm_us_scan_position())
        no_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="No",
                                       command=lambda: self.reject_us_scan_position())
        yes_button.grid(row=1, column=4)
        no_button.grid(row=2, column=4)

        # Create scanning location question
        view = self.get_US_scan_location()  # based on dicom filename
        scan_pos_ques = tkinter.Label(ques_frame, text='Is this a {} view?'.format(view), background='white')
        scan_pos_ques.grid(row=0, column=4)

        # Setup keyboard shortcuts
        self.master.bind("<Key>", self.process_key_press_view_selection)
        self.master.focus_set()  # Needed for keyboard shortcuts to work
        return [yes_button, no_button, scan_pos_ques, ques_frame]  # return handles to components to clean them up later

    def go_to_set_US_scan_location_view(self):
        """ GUI view for selecting the scanning position

        :return:
        """
        self.scan_buttons = [] # Needed to highlight the correct buttons according to the selected labels
        # Create frame as a placeholder
        misc_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        misc_button_frame.grid(column=4, row=12, rowspan=len(self.us_scan_positions)*3)

        # Create as many buttons as there are us scan positions
        for i, button_name in enumerate(self.us_scan_positions):
            scan_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text=button_name,
                                     command=partial(self.process_scan_position_button_press, button_name)) # partial is a method to create a function reference
            scan_button.grid(row=i, column=4)
            misc_button_frame.rowconfigure(i, pad=5)
            self.scan_buttons.append(scan_button)
        self.scan_buttons.append(misc_button_frame)

    def confirm_us_scan_position(self):
        """ Saves the us scan position when confirmed and goes to the labelling view

        :return:
        """
        self.destroy_scan_pos_question()
        view = self.get_US_scan_location()
        self.video_info.loc[self.video_number, 'scan location'] = view
        self.go_to_labelling_view()

    def reject_us_scan_position(self):
        """ When the us scan position is rejected, go to the view to set the us scan location

        :return:
        """
        self.destroy_scan_pos_question()
        self.go_to_set_US_scan_location_view()

    def destroy_scan_pos_question(self):
        """ Destroys all GUI components related to the scanning position question

        :return:
        """
        for component in self.scan_pos_question_components:
            component.destroy()

    def go_to_labelling_view(self):
        """ Initialize the view for labelling a frame

        :return:
        """
        self.labelling_buttons = []

        #Create paceholder for the buttons
        misc_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        misc_button_frame.grid(column=4, row=12, rowspan=len(self.pathology_labels)*3)

        # Create as many buttons as there are labels
        for i, button_name in enumerate(self.pathology_labels):
            label_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text='({}) '.format(i) + button_name,
                                          command=partial(self.process_label_button_press, button_name), anchor='w')
            label_button.grid(row=i, column=4)
            misc_button_frame.rowconfigure(i, pad=5)
            self.labelling_buttons.append(label_button)  # Save buttons handles to update them (e.g. color) later


        if self.label_mode.get() == 'multiple': # Button to clear the labels is only needed in multiple labelling mode
            clear_labels_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text='Clear labels',
                                                 command=self.process_clear_label_button)
            clear_labels_button.grid(row=i+1, column=4)
            misc_button_frame.rowconfigure(i+1, pad=50)
            self.labelling_buttons.append(clear_labels_button)

        # Setup keyboard shortcuts
        self.master.bind("<Key>", self.process_key_press_label_view)
        self.master.focus_set()

        self.labelling_buttons.append(misc_button_frame) # Add the frame to the end for cleaning it up later
        self.default_button_color = label_button.cget("background")  # Save button color to restore it later
        self.frame_num = 0
        self.update_frame()

    def process_clear_label_button(self):
        """ Clears the already selected labels for a frame

        :return:
        """
        self.restore_color_of_label_buttons()
        self.labels = []

    def restore_color_of_label_buttons(self):
        """ go back to the default label button color

        :return:
        """
        for label in self.labels:
            pathology_index = self.pathology_labels.index(label)
            pressed_button = self.labelling_buttons[pathology_index]
            pressed_button.configure(bg=self.default_button_color)

    def destroy_list_of_GUI_components(self, component_list):
        """ Destroys all the components that are in a list

        :param component_list: (list) A list of GUI components
        :return:
        """
        for component in component_list:
            component.destroy()

    def process_scan_position_button_press(self, view):
        """ Saves the us scan position after the button is selected

        :param view: (string) the us scan position
        :return:
        """
        self.video_info.loc[self.video_number, 'scan location'] = view
        for button in self.scan_buttons:
            button.destroy()
        self.go_to_labelling_view()

    def process_key_press_label_view(self, event):
        """ Process a key press for the label view

        :param event:
        :return:
        """
        if str.isnumeric(event.char):
            label_no = int(event.char)
            if label_no < len(self.pathology_labels):
                self.process_label_button_press(self.pathology_labels[int(event.char)])
            else:
                print('Number pressed exceeds the amount of labels')
        elif event.char == 'l':
            self.next_frame()
        elif event.char == 'k':
            self.previous_frame()

    def process_key_press_view_selection(self, event):
        """ Process a key press for the scan position question view

        :param event:
        :return:
        """
        if event.char == 'l':
            self.next_frame()
        elif event.char == 'k':
            self.previous_frame()

    def process_label_button_press(self, pathology):
        """ Process akey press in the labelling view

        :param pathology:
        :return:
        """
        if self.label_mode.get() == 'multiple':
            if not pathology in self.labels:
                self.highlight_label_button(pathology)
                self.labels.append(pathology)
            else:
                print('This label has already been added to this frame')
        else:
            self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label'] = pathology
            self.print_labelling_text(pathology)
            self.next_frame()

    def highlight_label_button(self, pathology):
        """ changes the color a of a button (to indicate what labels were already selected)

        :param pathology:
        :return:
        """
        pathology_index = self.pathology_labels.index(pathology)
        pressed_button = self.labelling_buttons[pathology_index]
        pressed_button.configure(bg='dark gray')

    def print_labelling_text(self, labels):
        """ Prints what labels were selected when going to the next frame

        :param labels: (list of strings) These strings will be printed below the figure
        :return:
        """
        self.label_text.destroy()
        self.label_text2.destroy()
        label_string = '{}'.format(labels)
        label_text = ' label saved for frame {} / {}'.format(self.frame_num + 1, len(self.frames))
        self.label_text = tkinter.Label(master=self.master, text=label_string, font=self.label_text_font_bold, background='white')
        self.label_text2 = tkinter.Label(master=self.master, text=label_text, font=self.label_text_font, background='white')
        self.label_text.grid(row=51, column=0, sticky='e')
        self.label_text2.grid(row=51, column=1, sticky='W')

    def save_data(self):
        """ Export the data in the DataFrames to a csv

        :return:
        """
        self.frame_info.to_csv(os.path.join(self.dicom_data_path, self.frame_output_file))
        self.video_info.to_csv(os.path.join(self.dicom_data_path, self.video_output_file))

    def get_US_scan_location(self):
        """ Retrieves the us scan location based on the filename

        :return:
        """
        view = self.dicom_file_names[self.video_number].split('_')[-1] # get everything after the underscore
        view = view.split('.')[0]  # Cut off the file extension if there is one
        return view

    def done(self):
        """
        Closes the GUI window whe the user confirms he is done
        :return:
        """

        self.exit_frame = tkinter.Frame(self.master, padx=10, background='white')
        self.exit_frame.grid(column=1, row=25)
        self.exit_frame.rowconfigure(1, pad=5)  # add padding for the buttons

        # Create text for the exit confirmation
        self.loading_text_font_bold = tkFont.Font(family='Segoe UI', size=18, weight='bold')
        self.close_text = tkinter.Label(master=self.exit_frame, text='All videos have been labeled. You can go back to labelling or exit',
                                        font=self.loading_text_font_bold, bg='white')
        self.close_text.grid(row=0, column=0, columnspan=2)

        # Create back and exit buttons
        back_button = tkinter.Button(master=self.exit_frame, height=1, width=self.buttonwidth, text="Back",
                                   command=lambda: self.clean_exit_prompt())
        exit_button = tkinter.Button(master=self.exit_frame, height=1, width=self.buttonwidth, text="Exit",
                                    command=lambda: self.exit())

        # Put the buttons on the edge of the columns to make them appear close together
        back_button.grid(row=1, column=0, sticky='e', padx=10)
        exit_button.grid(row=1, column=1, sticky='w', padx=10)

    def exit(self):
        """ Destroys all GUI components

        :return:
        """
        self.master.destroy()

    def clean_exit_prompt(self):
        """ When going back to labelling the done (exit) dialog is removed

        :return:
        """
        self.exit_frame.destroy()