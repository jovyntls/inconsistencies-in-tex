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

def run_compare_all(current_time):
    logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                       console_log_level=logging.INFO, has_file_handler=True)
    dirs = os.listdir(COMPILED_FOLDER)
    rows = []
    for arxiv_id in tqdm(dirs):
        result = convert_pdf_to_img.main(arxiv_id)
        # xelua_result = { f'xelua_{key}': val for key,val in result['xelua'].to_dict().items() }
        # xepdf_result = { f'xepdf_{key}': val for key,val in result['xepdf'].to_dict().items() }
        # result_as_row = { 'arxiv_id': arxiv_id } | xelua_result | xepdf_result
        # rows.append(result_as_row)
    LOGGER.info(f'logfile timestamp: {current_time}')
    # RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='arxiv_id')
    # LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
    # RESULTS_SUMMARY.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_imgcompare_results.csv'))


def run(run_for_id, do_convert, do_compare):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if run_for_id is None: run_compare_all(current_time)
    else: 
        # don't log to a file if running for only one
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
