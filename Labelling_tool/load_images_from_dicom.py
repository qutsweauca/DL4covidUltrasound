from pydicom import dcmread
from pydicom import pixel_data_handlers

def get_list_of_images_from_dicom_file(file_path):
    """ Loads all images from a DICOM file and returns them in a list. Performs image color space conversion from YBR_FULL_422 to RGB

    :param file_path: (string) The path of the DICOM file
    :return: list_of_images (list) A list with all the images in the DICOM file
    """
    df = dcmread(file_path)
    df_data = df.pixel_array
    list_of_images = [us_image_converting(df_data[i, :, :, :]) for i in range(df_data.shape[0])]
    # list_of_images = [df_data[i, :, :, :] for i in range(df_data.shape[0])][0:10] # Test code without image conversion and only loading subset of images
    return list_of_images

def us_image_converting(input_img, input_color_space='YBR_FULL_422', output_color_space='RGB'):
    """ Perform image color space conversion

    :param input_img: (nparray) The input image
    :param input_color_space: (string) The color space of the input image
    :param output_color_space: (string) The color space of the output image
    :return:
    """
    # (0028,0004) Photometric Interpretation. (for input_color_space)
    output_img = pixel_data_handlers.util.convert_color_space(input_img, input_color_space, output_color_space)

    return output_img
