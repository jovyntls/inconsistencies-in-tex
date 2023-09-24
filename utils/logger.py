import logging
import os

PIPELINE_LOGGER_ID = 'diff_test_tex_engines'
ANALYSIS_LOGGER_ID = 'pdf_comparison_analysis'
FORMATTER = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

def add_console_handler(logger, formatter, log_level=logging.INFO):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def add_file_handler(logger, formatter, log_filepath):
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def init_for_pipeline(logs_folder, timestamp):
    logger = logging.getLogger(PIPELINE_LOGGER_ID)
    logger.setLevel(logging.DEBUG)
    add_console_handler(logger, FORMATTER)
    log_filepath = os.path.join(logs_folder, f'{timestamp}_pipeline.log')
    add_file_handler(logger, FORMATTER, log_filepath)

def init_for_analysis(logs_folder, timestamp, has_file_handler=False, console_log_level=logging.INFO):
    logger = logging.getLogger(ANALYSIS_LOGGER_ID)
    logger.setLevel(logging.DEBUG)
    add_console_handler(logger, FORMATTER, console_log_level)
    if has_file_handler: 
        log_filepath = os.path.join(logs_folder, f'{timestamp}_analysis.log')
        add_file_handler(logger, FORMATTER, log_filepath)

def pad_with_char(string, char):
    chars_per_side = (60 - len(string) - 2) // 2
    extra_pad = '' if len(string)%2==0 else ' '
    delim_line = char*chars_per_side
    return f'{delim_line} {string} {extra_pad}{delim_line}'

PIPELINE_LOGGER = logging.getLogger(PIPELINE_LOGGER_ID)
ANALYSIS_LOGGER = logging.getLogger(ANALYSIS_LOGGER_ID)

