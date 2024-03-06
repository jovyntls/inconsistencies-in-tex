import os

PROJECT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "work", "fyp", "diff_test_tex_engines")
LOGS_FOLDER = os.path.join(PROJECT_ROOT, 'logs')
PROJECT_BIN = os.path.join(PROJECT_ROOT, 'bin')

DOWNLOAD_FOLDER = os.path.join(PROJECT_BIN, 'arxiv_tars')
EXTRACTED_FOLDER = os.path.join(PROJECT_BIN, 'arxiv_tars_extracted')
COMPILED_FOLDER = os.path.join(PROJECT_BIN, 'compiled_tex_pdf')
DIFFS_FOLDER = os.path.join(PROJECT_BIN, 'diff_pdfs')

YEAR_AND_MONTH = '2306'
NUM_ATTEMPTS = 3
TEX_FILE_DOWNLOAD_XPATH = '//*[@id="dlpage"]/dl'
# leave this empty if running for all
DOWNLOAD_BY_ARXIV_IDS = [ '2306.00036', '2306.00207', '2306.00028', '2306.00001', '2306.00002', '2306.00057', '2306.01691', '2306.00004', '2306.00022', '2306.01308' ]

PIXEL_TOLERANCE = 500

# for img comparison
CONVERTED_IMG_FOLDER = os.path.join(PROJECT_BIN, 'converted_img')
CONVERT_FIRST_N_PAGES = 3
CONVERT_LAST_N_PAGES = 3
