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

        # Label mode selection
        label_mode_frame = tkinter.Frame(self.master, background='white')
        label_mode_frame.grid(column=4, row=5, padx=10, sticky='w')

        self.label_mode = tkinter.StringVar()
        self.label_mode.set('multiple')

        label_mode_text = tkinter.Label(master=label_mode_frame, text='Label mode', background='white')
        label_mode_text.grid(sticky='w')

        single_label_rad_button = tkinter.Radiobutton(master=label_mode_frame, text='Single', variable=self.label_mode, value='single',
                                                      bg='white')
        single_label_rad_button.grid(sticky='w')

        multiple_labels_rad_button = tkinter.Radiobutton(master=label_mode_frame, text='Multiple', variable=self.label_mode, value='multiple',
                                                         bg='white')
        multiple_labels_rad_button.grid(sticky='w')

    def next_frame(self):
        if self.label_mode.get() == 'multiple':
            if len(self.labels) > 0:
                multiple_label_text = ', '.join(self.labels)
                self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label'] = multiple_label_text
                self.print_labelling_text(multiple_label_text)
        if self.frame_num < (len(self.frames)-1):
            self.restore_color_of_label_buttons()
            self.frame_num += 1
            self.update_labels_attribute()  # To color buttons according to labels that were already done
            for pathology in self.labels:
                self.highlight_label_button(pathology)
            self.update_frame()
        else:
            self.go_to_next_video()

    def previous_frame(self):
        if self.frame_num > 0:
            self.restore_color_of_label_buttons()  # Go back to the default button color
            self.frame_num -= 1
            self.update_labels_attribute()
            for pathology in self.labels:  # Highlights the buttons of labels added to the frame previously
                self.highlight_label_button(pathology)
            self.update_frame()

    def update_labels_attribute(self):
        pathology_labels = self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label']

        if len(pathology_labels) == 0:
            self.labels = []
        else:
            pathology_labels = pathology_labels.replace(' ', '', 1)
            self.labels = pathology_labels.split(',')

    def go_to_next_video(self):
        self.save_data()
        if self.video_number == len(self.dicom_file_names)-1:
            self.done()
        else:
            self.video_number += 1
            self.show_loading_text()
            self.init_for_next_us_sequence()
            self.remove_loading_text()
            self.update_frame()

    def go_to_scan_position_question(self):

        ques_frame = tkinter.Frame(self.master, padx=10, background='white')
        ques_frame.grid(column=4, row=8)
        ques_frame.rowconfigure(0, pad=5)
        ques_frame.rowconfigure(1, pad=5)
        ques_frame.rowconfigure(2, pad=5)

        # Create scanning location buttons and question
        yes_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="Yes",
                                        command=lambda: self.confirm_us_scan_position())
        no_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="No",
                                       command=lambda: self.reject_us_scan_position())
        yes_button.grid(row=1, column=4)
        no_button.grid(row=2, column=4)

        view = self.get_US_scan_location()
        scan_pos_ques = tkinter.Label(ques_frame, text='Is this a {} view?'.format(view), background='white')
        scan_pos_ques.grid(row=0, column=4)
        self.master.bind("<Key>", self.process_key_press_view_selection)
        self.master.focus_set()
        return [yes_button, no_button, scan_pos_ques, ques_frame]  # return handles to components to clean them up later

    def go_to_set_US_scan_location_view(self):
        self.scan_buttons = []
        misc_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        misc_button_frame.grid(column=4, row=12, rowspan=len(self.us_scan_positions)*3)
        for i, button_name in enumerate(self.us_scan_positions):
            scan_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text=button_name,
                                     command=partial(self.process_scan_position_button_press, button_name))
            scan_button.grid(row=i, column=4)
            misc_button_frame.rowconfigure(i, pad=5)
            self.scan_buttons.append(scan_button)
        self.scan_buttons.append(misc_button_frame)

    def confirm_us_scan_position(self):
        self.destroy_scan_pos_question()
        # self.destroy_list_of_GUI_components(self.scan_pos_question_components)
        view = self.get_US_scan_location()
        self.video_info.loc[self.video_number, 'scan location'] = view
        self.go_to_labelling_view()

    def reject_us_scan_position(self):
        self.destroy_scan_pos_question()
        # self.destroy_list_of_GUI_components(self.scan_pos_question_components)
        self.go_to_set_US_scan_location_view()

    def destroy_scan_pos_question(self):
        for component in self.scan_pos_question_components:
            component.destroy()

    def go_to_labelling_view(self):
        self.labelling_buttons = []
        misc_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        misc_button_frame.grid(column=4, row=12, rowspan=len(self.pathology_labels)*3)
        for i, button_name in enumerate(self.pathology_labels):
            label_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text='({}) '.format(i) + button_name,
                                          command=partial(self.process_label_button_press, button_name), anchor='w')
            label_button.grid(row=i, column=4)
            misc_button_frame.rowconfigure(i, pad=5)
            self.labelling_buttons.append(label_button)
        if self.label_mode.get() == 'multiple':
            clear_labels_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text='Clear labels',
                                                 command=self.process_clear_label_button)
            clear_labels_button.grid(row=i+1, column=4)
            misc_button_frame.rowconfigure(i+1, pad=50)
            self.labelling_buttons.append(clear_labels_button)
        self.master.bind("<Key>", self.process_key_press_label_view)
        self.master.focus_set()
        self.labelling_buttons.append(misc_button_frame)
        self.default_button_color = label_button.cget("background")  # Save button color to restore it later
        self.frame_num = 0
        self.update_frame()

    def process_clear_label_button(self):
        self.restore_color_of_label_buttons()
        self.labels = []

    def restore_color_of_label_buttons(self):
        for label in self.labels:
            pathology_index = self.pathology_labels.index(label)
            pressed_button = self.labelling_buttons[pathology_index]
            pressed_button.configure(bg=self.default_button_color)

    def destroy_list_of_GUI_components(self, component_list):
        for component in component_list:
            component.destroy()

    def process_scan_position_button_press(self, view):
        self.video_info.loc[self.video_number, 'scan location'] = view
        for button in self.scan_buttons:
            button.destroy()
        self.go_to_labelling_view()

    def process_key_press_label_view(self, event):
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
        if event.char == 'l':
            self.next_frame()
        elif event.char == 'k':
            self.previous_frame()

    def process_label_button_press(self, pathology):
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
        pathology_index = self.pathology_labels.index(pathology)
        pressed_button = self.labelling_buttons[pathology_index]
        pressed_button.configure(bg='dark gray')

    def print_labelling_text(self, labels):
        self.label_text.destroy()
        self.label_text2.destroy()
        label_string = '{}'.format(labels)
        label_text = ' label saved for frame {} / {}'.format(self.frame_num + 1, len(self.frames))
        self.label_text = tkinter.Label(master=self.master, text=label_string, font=self.label_text_font_bold, background='white')
        self.label_text2 = tkinter.Label(master=self.master, text=label_text, font=self.label_text_font, background='white')
        self.label_text.grid(row=51, column=0, sticky='e')
        self.label_text2.grid(row=51, column=1, sticky='W')

    def save_data(self):
        self.frame_info.to_csv(os.path.join(self.dicom_data_path, self.frame_output_file))
        self.video_info.to_csv(os.path.join(self.dicom_data_path, self.video_output_file))

    def get_US_scan_location(self):
        view = self.dicom_file_names[self.video_number].split('_')[-1]
        view = view.split('.')[0]
        return view

    def done(self):
        """Destroys the gui window as soon as the database is saved"""
        self.exit_frame = tkinter.Frame(self.master, padx=10, background='white')
        self.exit_frame.grid(column=1, row=25)
        # ques_frame.rowconfigure(0, pad=5)
        self.exit_frame.rowconfigure(1, pad=5)
        # ques_frame.rowconfigure(2, pad=5)

        self.loading_text_font_bold = tkFont.Font(family='Segoe UI', size=18, weight='bold')
        self.close_text = tkinter.Label(master=self.exit_frame, text='All videos have been labeled. You can go back to labelling or exit',
                                        font=self.loading_text_font_bold, bg='white')
        self.close_text.grid(row=0, column=0, columnspan=2)

        # Create scanning location buttons and question
        back_button = tkinter.Button(master=self.exit_frame, height=1, width=self.buttonwidth, text="Back",
                                   command=lambda: self.clean_exit_prompt())
        exit_button = tkinter.Button(master=self.exit_frame, height=1, width=self.buttonwidth, text="Exit",
                                    command=lambda: self.exit())
        back_button.grid(row=1, column=0, sticky='e', padx=10)
        exit_button.grid(row=1, column=1, sticky='w', padx=10)
        # self.master.update_idletasks()

    def exit(self):
        self.master.destroy()

    def clean_exit_prompt(self):
        self.exit_frame.destroy()