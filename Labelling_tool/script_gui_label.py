import tkinter
import argparse
from class_label_gui import LabelGUI
from pydicom import dcmread
import get_files_with_extension

parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, required=True,
                    help="Root directory under which the subject directories are stored")

parser.add_argument("--first_video", type=int, required=True,
                    help="Index of the first subject to be processed")
arguments = parser.parse_args()

gui_window = tkinter.Tk()
gui_window.configure(background='white')
LabelGUI(master=gui_window, first_video=arguments.first_video, dicom_data_path=arguments.data_path)
gui_window.mainloop()
