import os
from logger import Logger, Log_level
import get_tex_files
import extract_compressed_sources
import compare_tex_files

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

get_tex_files.main(20, DOWNLOAD_FOLDER, LOGGER)
extract_compressed_sources.main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER, LOGGER)
compare_tex_files.main(EXTRACTED_FOLDER, COMPILED_FOLDER, DIFFS_FOLDER, LOGGER)

