import os
import pandas as pd

from utils.logger import Logger
from utils import tex_engine_utils
from config import LOG_LEVEL, DOWNLOAD_FOLDER, EXTRACTED_FOLDER, COMPILED_FOLDER, DIFFS_FOLDER
import get_tex_files
import extract_compressed_sources
import compile_tex_files
import diff_pdfs

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(COMPILED_FOLDER, exist_ok=True)
os.makedirs(DIFFS_FOLDER, exist_ok=True)

LOGGER = Logger(LOG_LEVEL)

results_column_names = [ 'arxiv_id', 'entrypoint' ] + tex_engine_utils.TEX_ENGINES + [f'{e1}<>{e2}' for e1, e2 in tex_engine_utils.DIFF_ENGINE_PAIRS]
RESULTS = pd.DataFrame(columns=results_column_names)
RESULTS = RESULTS.set_index('arxiv_id')

get_tex_files.main(DOWNLOAD_FOLDER, LOGGER)
extract_compressed_sources.main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER, LOGGER)
RESULTS = compile_tex_files.main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS, LOGGER)
RESULTS = diff_pdfs.main(COMPILED_FOLDER, DIFFS_FOLDER, RESULTS, LOGGER)

print(RESULTS.to_string())

