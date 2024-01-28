import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from img_comparison import convert_pdf_to_img, compare_imgs

LOGGER = logger.COMPARISON_LOGGER

def convert_for_all():
    LOGGER.info('converting PDFs to image...')
    for arxiv_id in tqdm(['2306.00002', '2306.00003']):
    # for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER)):
        convert_pdf_to_img.main(arxiv_id)

def compare_for_all():
    dirs = os.listdir(COMPILED_FOLDER)
    dirs = ['2306.00002', '2306.00003']
    rows = []
    LOGGER.info('running image comparisons...')
    for arxiv_id in tqdm(dirs):
        result = compare_imgs.main(arxiv_id)
        for page, page_results in result.items():
            page_results['identifier'] = f'{arxiv_id}_{page}'
            rows.append(page_results)
    RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='identifier')
    LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
    return RESULTS_SUMMARY


def run(run_for_id, do_convert, do_compare):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if run_for_id is None: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.INFO, has_file_handler=True)
        LOGGER.info(f'logfile timestamp: {current_time}')
        if do_convert: convert_for_all()
        if do_compare: 
            results = compare_for_all()
            results.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_imgcompare.csv'))
    else: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.DEBUG, has_file_handler=False)
        arxiv_id = f'{YEAR_AND_MONTH}.{run_for_id}'
        if do_convert: convert_pdf_to_img.main(arxiv_id)
        if do_compare: compare_imgs.main(arxiv_id)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run image comparison')
    parser.add_argument('-id', nargs='?', default=None, help="arxiv_id to run on (runs on all PDFs if not specified)")
    parser.add_argument('-convert', action='store_true', help="run conversion (of pdf to img) only")
    parser.add_argument('-compare', action='store_true', help="run image comparison only")
    args = parser.parse_args()

    do_both = not args.compare and not args.convert
    do_compare = args.compare or do_both
    do_convert = args.convert or do_both
    run(args.id, do_convert, do_compare)
