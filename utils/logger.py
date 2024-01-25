import logging
import os

PIPELINE_LOGGER_ID = 'pipeline'
ANALYSIS_LOGGER_ID = 'analysis'
COMPARISON_LOGGER_ID = 'imgcompare'

FORMATTER = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

def add_console_handler(logger, log_level=logging.INFO):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(FORMATTER)
    logger.addHandler(console_handler)

def add_file_handler(logger, log_filepath):
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FORMATTER)
    logger.addHandler(file_handler)

# analysis logger - console 
def init_logger(logger_id, logs_folder, timestamp, console_log_level, has_file_handler):
    logger = logging.getLogger(logger_id)
    logger.setLevel(logging.DEBUG)
    add_console_handler(logger, console_log_level)
    if has_file_handler: 
        log_filepath = os.path.join(logs_folder, f'{timestamp}_{logger_id}.log')
        add_file_handler(logger, log_filepath)

def pad_with_char(string, char):
    chars_per_side = (60 - len(string) - 2) // 2
    extra_pad = '' if len(string)%2==0 else ' '
    delim_line = char*chars_per_side
    return f'{delim_line} {string} {extra_pad}{delim_line}'

PIPELINE_LOGGER = logging.getLogger(PIPELINE_LOGGER_ID)
ANALYSIS_LOGGER = logging.getLogger(ANALYSIS_LOGGER_ID)
COMPARISON_LOGGER = logging.getLogger(COMPARISON_LOGGER_ID)

