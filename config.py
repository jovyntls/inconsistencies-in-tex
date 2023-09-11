import os

PROJECT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "work", "fyp", "diff_test_tex_engines")
LOGS_FOLDER = os.path.join(PROJECT_ROOT, 'logs')

DOWNLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars')
EXTRACTED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/arxiv_tars_extracted')
COMPILED_FOLDER = os.path.join(PROJECT_ROOT, 'bin/compiled_tex_pdf')
DIFFS_FOLDER = os.path.join(PROJECT_ROOT, 'bin/diff_pdfs')


NUM_ATTEMPTS = 50
TEX_FILE_DOWNLOAD_URL = 'https://arxiv.org/list/cs.IT/2308?skip=0&show=' + str(NUM_ATTEMPTS)
TEX_FILE_DOWNLOAD_XPATH = '//*[@id="dlpage"]/dl'

PIXEL_TOLERANCE = 2000
