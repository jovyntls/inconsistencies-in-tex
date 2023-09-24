import logging
import os

PIPELINE_LOGGER_ID = 'diff_test_tex_engines'
ANALYSIS_LOGGER_ID = 'pdf_comparison_analysis'

def init(logger_id, logs_folder, timestamp, tag=''):
    # Configure the logging settings
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    log_name = f'{timestamp}_{tag}' if tag != '' else f'{timestamp}'
    log_filepath = os.path.join(logs_folder, f'{log_name}.log')

    # Create a logger
    logger = logging.getLogger(logger_id)
    logger.setLevel(logging.DEBUG)

    # Create a console handler and set the level to INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Create a file handler and set the level to DEBUG
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and set it for the handlers
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def init_for_pipeline(logs_folder, timestamp):
    return init(PIPELINE_LOGGER_ID, logs_folder, timestamp, tag='pipeline')

def init_for_analysis(logs_folder, timestamp):
    return init(ANALYSIS_LOGGER_ID, logs_folder, timestamp, tag='analysis')

PIPELINE_LOGGER = logging.getLogger(PIPELINE_LOGGER_ID)
ANALYSIS_LOGGER = logging.getLogger(ANALYSIS_LOGGER_ID)

