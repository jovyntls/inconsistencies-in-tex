import os
import pandas as pd

from logger import Logger, Log_level
import tex_engine_utils

import get_tex_files
import extract_compressed_sources
import compile_tex_files
import diff_pdfs

PROJECT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "work", "fyp", "exploration", "diff_test_tex_engines")
DOWNLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars')
EXTRACTED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars_extracted')
COMPILED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/compiled_tex_pdf')
DIFFS_FOLDER = os.path.join(PROJECT_ROOT, 'bin/diff_pdfs')

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(COMPILED_FOLDER, exist_ok=True)
os.makedirs(DIFFS_FOLDER, exist_ok=True)

LOGGER = Logger(Log_level.INFO)

results_column_names = [ 'arxiv_id', 'entrypoint' ] + tex_engine_utils.TEX_ENGINES + [f'{e1}<>{e2}' for e1, e2 in tex_engine_utils.DIFF_ENGINE_PAIRS]
RESULTS = pd.DataFrame(columns=results_column_names)
RESULTS = RESULTS.set_index('arxiv_id')

get_tex_files.main(3, DOWNLOAD_FOLDER, LOGGER)
extract_compressed_sources.main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER, LOGGER)
RESULTS = compile_tex_files.main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS, LOGGER)
RESULTS = diff_pdfs.main(COMPILED_FOLDER, DIFFS_FOLDER, RESULTS, LOGGER)

pd.display(RESULTS)

