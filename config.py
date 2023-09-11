import os

PROJECT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "work", "fyp", "diff_test_tex_engines")
LOGS_FOLDER = os.path.join(PROJECT_ROOT, 'logs')

DOWNLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars')
EXTRACTED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars_extracted')
COMPILED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/compiled_tex_pdf')
DIFFS_FOLDER = os.path.join(PROJECT_ROOT, 'bin/diff_pdfs')

YEAR_AND_MONTH = '2306'
NUM_ATTEMPTS = 5
TEX_FILE_DOWNLOAD_XPATH = '//*[@id="dlpage"]/dl'

SHOULD_SKIP_COMPILE = False
SKIP_COMPILE_FOR = ['{IEEEtran}']

PIXEL_TOLERANCE = 2000
