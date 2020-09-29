import tkinter
import argparse
from class_label_gui import LabelGUI
from pydicom import dcmread
import get_files_with_extension
from tkinter import filedialog

# Pop up dialog for selecting a folder
root = tkinter.Tk()
root.withdraw()  # Do not show the root tkinter dialog
directory = filedialog.askdirectory()
root.destroy()

# Start the GUI
gui_window = tkinter.Tk()
gui_window.configure(background='white')
LabelGUI(master=gui_window, first_video=0, dicom_data_path=directory)
gui_window.mainloop()
