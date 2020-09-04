import tkinter
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from get_files_with_extension import get_files_with_extension
from label_gui_plot import get_list_of_images_from_dicom_file
import pandas as pd
from functools import partial


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
            dicom_data_path (str): main path where the DICOM files are stores
            file_extension (str): extension of the DICOM files containing the images.
        """
        # self.label_mode = 'multiple'
        self.labels = []

        # Initializing some stuff
        self.master = master
        self.video_number = first_video
        self.dicom_data_path = dicom_data_path
        self.video_info = pd.DataFrame(columns=['video file', 'scan location'])
        self.frame_info = pd.DataFrame(columns=['video file', 'pathology label'])
        self.frame_index_start = 0
        self.us_scan_positions = ('RANT', 'LANT', 'LPL',  'RPL', 'LPU', 'RPU')
        self.first_row_multiple_buttons = 15
        self.pathology_labels = ['Normal', 'Collapse', 'Consolidation', 'APO / Int. Syndrome', 'Pneumothorax', 'Effusion', 'B-lines', 'Pleural thickening', 'Irregular pleura']
        self.figure = plt.figure(figsize=(10, 8))
        self.figure.set_tight_layout(True)
        self.buttonwidth = 15
        self.create_output_filename()

        # Getting and storing DICOM file names
        self.dicom_file_names = get_files_with_extension(self.dicom_data_path, file_extension)
        self.video_info.loc[:, 'video file'] = self.dicom_file_names

        self.init_GUI()

    def create_output_filename(self):
        suffix = os.path.split(self.dicom_data_path)[-1]
        self.frame_output_file = 'frame_info_' + suffix + '.csv'
        self.video_output_file = 'video_info_' + suffix + '.csv'
        self.frame_output_file = self.check_for_duplicate_filename(self.dicom_data_path, self.frame_output_file)
        self.video_output_file = self.check_for_duplicate_filename(self.dicom_data_path, self.video_output_file)

    def check_for_duplicate_filename(self, datapath, filename):
        print(os.path.join(datapath, filename))
        if os.path.exists(os.path.join(datapath, filename)):
            filename = filename[:-4] + '_1' + filename[-4:]

        i = 2
        while os.path.exists(os.path.join(datapath, filename)):
            filename = filename[:-6] + '_' + str(i) + filename[-4:]
            i += 1
        return filename

    def init_GUI(self) -> None:
        """Create GUI canvas and buttons"""
        self.figure.clf()

        # Create plotting canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=50)
        self.init_data_for_GUI()
        self.plot_frame()

        self.add_standard_buttons()
        self.scan_pos_question_components = self.go_to_scan_position_question()  # Start with scanning position

    def init_data_for_GUI(self):
        self.frames = get_list_of_images_from_dicom_file(self.dicom_file_names[self.video_number])[0:10]

        self.frame_index = self.generate_frame_index(self.frame_index_start, len(self.frames))
        frame_index_df = pd.DataFrame(columns=['video file'], data=[self.dicom_file_names[self.video_number]] * len(self.frames))
        self.frame_info = self.frame_info.append(frame_index_df).fillna('')
        self.frame_info.reset_index(drop=True, inplace=True)

        self.frame_num = 0
        self.frame_index_start = frame_index_df.shape[0]

    def init_for_next_video(self):
        self.init_data_for_GUI()
        self.destroy_list_of_GUI_components(self.labelling_buttons)
        self.scan_pos_question_components = self.go_to_scan_position_question()

    def generate_frame_index(self, current, no_frames):
        return range(current, current + no_frames)

    def plot_frame(self):
        plt.gca()
        plt.imshow(self.frames[self.frame_num])
        plt.xticks([])
        plt.yticks([])
        plt.title('Frame {} / {}'.format(self.frame_num + 1, len(self.frames)))
        self.canvas.draw()

    def update_frame(self):
        self.figure.axes[0].images[0].set_array(self.frames[self.frame_num])
        plt.title('Frame {} / {}'.format(self.frame_num + 1, len(self.frames)))
        self.canvas.draw()

    def add_standard_buttons(self):
        std_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        std_button_frame.grid(column=1, row=43)
        std_button_frame.rowconfigure(0, pad=5)
        std_button_frame.rowconfigure(1, pad=5)
        std_button_frame.rowconfigure(2, pad=5)

        next_frame_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Next Frame",
                                       command=lambda: self.next_frame())
        previous_frame_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Previous Frame",
                                       command=lambda: self.previous_frame())
        next_frame_button.grid(row=0, column=1)
        previous_frame_button.grid(row=1, column=1)

        # Create save button
        save_button = tkinter.Button(master=std_button_frame, height=1, width=self.buttonwidth, text="Save",
                                     command=lambda: self.save_data())
        save_button.grid(row=2, column=1)

        label_mode_frame = tkinter.Frame(self.master, background='white')
        label_mode_frame.grid(column=1, row=5, padx=10, sticky='w')
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
            self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label'] = ', '.join(self.labels)
            self.restore_color_of_label_buttons()
            self.labels = []
        if self.frame_num < (len(self.frames)-1):
            self.frame_num += 1
            self.update_frame()
        else:
            self.go_to_next_video()

    def previous_frame(self):
        if self.frame_num > 0:
            self.frame_num -= 1
            self.update_frame()

    def go_to_next_video(self):
        self.save_data()

        self.video_number += 1
        self.init_for_next_video()
        self.update_frame()

    def go_to_scan_position_question(self):

        ques_frame = tkinter.Frame(self.master, padx=10, background='white')
        ques_frame.grid(column=1, row=8)
        ques_frame.rowconfigure(0, pad=5)
        ques_frame.rowconfigure(1, pad=5)
        ques_frame.rowconfigure(2, pad=5)

        # Create scanning location buttons and question
        yes_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="Yes",
                                        command=lambda: self.confirm_us_scan_position())
        no_button = tkinter.Button(master=ques_frame, height=1, width=self.buttonwidth, text="No",
                                       command=lambda: self.reject_us_scan_position())
        yes_button.grid(row=1, column=1)
        no_button.grid(row=2, column=1)

        view = self.get_US_scan_location()
        scan_pos_ques = tkinter.Label(ques_frame, text='Is this a {} view?'.format(view), background='white')
        scan_pos_ques.grid(row=0, column=1)
        return [yes_button, no_button, scan_pos_ques, ques_frame]  # return handles to components to clean them up later

    def go_to_set_US_scan_location_view(self):
        self.scan_buttons = []
        misc_button_frame = tkinter.Frame(self.master, padx=10, background='white')
        misc_button_frame.grid(column=1, row=12, rowspan=len(self.us_scan_positions)*3)
        for i, button_name in enumerate(self.us_scan_positions):
            print(type(button_name))
            scan_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text=button_name,
                                     command=partial(self.process_scan_position_button_press, button_name))
            scan_button.grid(row=i, column=1)
            misc_button_frame.rowconfigure(i, pad=5)
            self.scan_buttons.append(scan_button)
        self.scan_buttons.append(misc_button_frame)

    def confirm_us_scan_position(self):
        self.destroy_scan_pos_question()
        # self.destroy_list_of_GUI_components(self.scan_pos_question_components)
        view = self.get_US_scan_location()
        self.video_info.loc[self.video_number, 'scan location'] = view
        self.go_to_labelling_view()
        print(self.video_info)

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
        misc_button_frame.grid(column=1, row=12, rowspan=len(self.pathology_labels)*3)
        for i, button_name in enumerate(self.pathology_labels):
            label_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text=button_name,
                                          command=partial(self.process_label_button_press, button_name))
            label_button.grid(row=i, column=1)
            misc_button_frame.rowconfigure(i, pad=5)
            self.labelling_buttons.append(label_button)
        if self.label_mode.get() == 'multiple':
            clear_labels_button = tkinter.Button(master=misc_button_frame, height=1, width=self.buttonwidth, text='Clear labels',
                                                 command=self.process_clear_label_button)
            clear_labels_button.grid(row=i+1, column=1)
            misc_button_frame.rowconfigure(i+1, pad=50)
            self.labelling_buttons.append(clear_labels_button)
        self.labelling_buttons.append(misc_button_frame)
        self.default_button_color = label_button.cget("background") # Save button color to restore it later
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
            print('destroying {}'.format(component))
            component.destroy()

    def process_scan_position_button_press(self, view):
        print(view)
        self.video_info.loc[self.video_number, 'scan location'] = view
        for button in self.scan_buttons:
            print('destroying {}'.format(button))
            button.destroy()
        self.go_to_labelling_view()
        print(self.video_info)

    def process_label_button_press(self, pathology):
        print(self.label_mode.get())
        if self.label_mode.get() == 'multiple':
            if not pathology in self.labels:
                pathology_index = self.pathology_labels.index(pathology)
                pressed_button = self.labelling_buttons[pathology_index]
                pressed_button.configure(bg='dark gray')
                self.labels.append(pathology)
            else:
                print('This label has already been added to this frame')
        else:
            self.frame_info.loc[self.frame_index[self.frame_num], 'pathology label'] = pathology
            self.next_frame()

    def save_data(self):
        self.frame_info.to_csv(os.path.join(self.dicom_data_path, self.frame_output_file))
        self.video_info.to_csv(os.path.join(self.dicom_data_path, self.video_output_file))

    def get_US_scan_location(self):
        view = self.dicom_file_names[self.video_number].split('_')[-1]
        return view

    def on_close(self):
        """Destroys the gui window as soon as the database is saved"""
        self.master.destroy()
