import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from img_comparison import convert_pdf_to_img

LOGGER = logger.COMPARISON_LOGGER

def run_compare_one(arxiv_id_suffix, should_save, current_time):
    # don't log to a file if running for only one
    logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                       console_log_level=logging.DEBUG, has_file_handler=False)

    arxiv_id = f'{YEAR_AND_MONTH}.{arxiv_id_suffix}'
    convert_pdf_to_img.main(arxiv_id)
    if should_save:
        print('save')

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


def run(args):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if args.id is None: run_compare_all(current_time)
    else: run_compare_one(args.id, args.save, current_time)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run image comparison')
    parser.add_argument('-save', action='store_true', help="save results to a file")
    parser.add_argument('-id', nargs='?', default=None, help="arxiv_id to run on (runs on all PDFs if not specified)")
    args = parser.parse_args()

    # leggooooooooooooooooo
    run(args)
