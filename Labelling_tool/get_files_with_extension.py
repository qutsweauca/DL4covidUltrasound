import os

def get_files_with_extension(folder_name: str, extension: str) -> list:
    """ Get all file names in folder with a specified extension
    Arguments:
        folder_name (str): name of the folder in which the files have to be selected
        extension (str): extension of the files to be selected
    Returns:
        file_names (list): list of file names that meet the extension requirement
    """
    file_names = []
    for path, _, files in os.walk(folder_name):
        for file in files:
            if file.endswith(extension):
                file_names.append(os.path.join(path, file))
    return file_names

def get_files_without_extension(folder_name: str) -> list:
    """ Get all file names in folder without an extension
    Arguments:
        folder_name (str): name of the folder in which the files have to be selected
    Returns:
        file_names (list): list of file names that meet the extension requirement
    """
    file_names = []
    for path, _, files in os.walk(folder_name):
        for file in files:
            if file.find('.') < 0:
                file_names.append(os.path.join(path, file))
    return file_names