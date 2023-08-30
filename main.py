import os
import pandas as pd

from utils import tex_engine_utils, logger
from config import LOGS_FOLDER, DOWNLOAD_FOLDER, EXTRACTED_FOLDER, COMPILED_FOLDER, DIFFS_FOLDER, NUM_ATTEMPTS, TEX_FILE_DOWNLOAD_URL, PIXEL_TOLERANCE
import get_tex_files
import extract_compressed_sources
import compile_tex_files
import diff_pdfs
import diff_pdfs_orange_blue

# set up logging
os.makedirs(LOGS_FOLDER, exist_ok=True)
logger.init(LOGS_FOLDER)
LOGGER = logger.LOGGER

# create dirs
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(COMPILED_FOLDER, exist_ok=True)
os.makedirs(DIFFS_FOLDER, exist_ok=True)

# set up result dataframe
results_column_names = [ 'arxiv_id', 'entrypoint' ] + tex_engine_utils.TEX_ENGINES + [f'{e1[:-5]}<>{e2[:-5]}' for e1, e2 in tex_engine_utils.DIFF_ENGINE_PAIRS]
RESULTS = pd.DataFrame(columns=results_column_names)
RESULTS = RESULTS.set_index('arxiv_id')

# run pipeline
LOGGER.info(f'running pipeline with params: {NUM_ATTEMPTS=}, {PIXEL_TOLERANCE=}, {TEX_FILE_DOWNLOAD_URL=}')
get_tex_files.main(DOWNLOAD_FOLDER)
extract_compressed_sources.main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER)
RESULTS = compile_tex_files.main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS)
RESULTS = diff_pdfs.main(COMPILED_FOLDER, DIFFS_FOLDER, RESULTS)
RESULTS = diff_pdfs_orange_blue.main(RESULTS)

LOGGER.info('results:\n' + RESULTS.to_string())

