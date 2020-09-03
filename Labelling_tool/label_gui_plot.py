import matplotlib.pyplot as plt
import os
from pydicom import dcmread
from pydicom import pixel_data_handlers

def get_list_of_images_from_dicom_file(file_path):
    df = dcmread(file_path)
    df_data =df.pixel_array
    list_of_images = [us_image_converting(df_data[i, :, :, :]) for i in range(df_data.shape[0])]
    # list_of_images = [df_data[i, :, :, :] for i in range(df_data.shape[0])]
    return list_of_images

def us_image_converting(input_img, type_img='YBR_FULL_422', output_color_space='RGB'):

    # (0028,0004) Photometric Interpretation. (for type_img)
    output_img = pixel_data_handlers.util.convert_color_space(input_img, type_img, output_color_space)

    return output_img
