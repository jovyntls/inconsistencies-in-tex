import logging
import os

def init(logs_folder, timestamp):
    # Configure the logging settings
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    log_filename = os.path.join(logs_folder, f'{timestamp}.log')

    # Create a logger
    logger = logging.getLogger('diff_test_tex_engines')
    logger.setLevel(logging.DEBUG)

    # Create a console handler and set the level to INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Create a file handler and set the level to DEBUG
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and set it for the handlers
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

LOGGER = logging.getLogger('diff_test_tex_engines')

