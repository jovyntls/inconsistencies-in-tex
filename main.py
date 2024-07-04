import os
import logging
import pandas as pd
from datetime import datetime

from utils import tex_engine_utils, logger
from config import COMPILED_FOLDER_2020, LOGS_FOLDER, DOWNLOAD_FOLDER, EXTRACTED_FOLDER, COMPILED_FOLDER, DIFFS_FOLDER, NUM_ATTEMPTS, PROJECT_BIN, YEAR_AND_MONTH, PIXEL_TOLERANCE, DOWNLOAD_BY_ARXIV_IDS
from pipeline import get_tex_files, extract_compressed_sources, compile_tex_files, diff_pdfs

# set up logging
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs(LOGS_FOLDER, exist_ok=True)
logger.init_logger(logger.PIPELINE_LOGGER_ID, LOGS_FOLDER, current_time,
                   console_log_level=logging.INFO, has_file_handler=True)
LOGGER = logger.PIPELINE_LOGGER
LOGGER.info(f'{LOGS_FOLDER=}')
LOGGER.info(f'{PROJECT_BIN=}')

# create dirs
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(COMPILED_FOLDER, exist_ok=True)
os.makedirs(DIFFS_FOLDER, exist_ok=True)

# set up result dataframe
results_column_names = [ 'arxiv_id', 'entrypoint', 'documentclass', 'docclass_params' ] + tex_engine_utils.TEX_ENGINES + [f'{e1}<>{e2}' for e1, e2 in tex_engine_utils.DIFF_ENGINE_PAIRS]
RESULTS = pd.DataFrame(columns=results_column_names)
RESULTS = RESULTS.set_index('arxiv_id')

# run pipeline
LOGGER.info(f'running pipeline with params: {NUM_ATTEMPTS=}, {YEAR_AND_MONTH=}, {PIXEL_TOLERANCE=}, {DOWNLOAD_BY_ARXIV_IDS=}')
get_tex_files.main(DOWNLOAD_FOLDER, download_by_arxiv_ids=DOWNLOAD_BY_ARXIV_IDS)
extract_compressed_sources.main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER)
RESULTS = compile_tex_files.main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS)
RESULTS = diff_pdfs.main(COMPILED_FOLDER, COMPILED_FOLDER_2020, DIFFS_FOLDER, RESULTS)

LOGGER.debug('results as csv:\n' + RESULTS.to_csv())
LOGGER.info('results:\n' + RESULTS.to_string())
RESULTS.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_results.csv'))


