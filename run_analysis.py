import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from analysis import count_pdf_pages, compare_text_similarity, count_compiled_pdfs
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS

COMPARE_ALL = 'COMPARE_ALL'
LOGGER = logger.ANALYSIS_LOGGER

def run_compare_one(arxiv_id_suffix, should_save, current_time):
    # don't log to a file if running for only one
    logger.init_logger(logger.ANALYSIS_LOGGER_ID, LOGS_FOLDER, current_time,
                       console_log_level=logging.DEBUG, has_file_handler=False)

    arxiv_id = f'{YEAR_AND_MONTH}.{arxiv_id_suffix}'
    compare_text_similarity.main(arxiv_id)
    if should_save:
        compare_text_similarity.extract_pdf_text_to_save_file(arxiv_id)

def run_compare_all(current_time):
    logger.init_logger(logger.ANALYSIS_LOGGER_ID, LOGS_FOLDER, current_time,
                       console_log_level=logging.INFO, has_file_handler=True)
    dirs = os.listdir(COMPILED_FOLDER)
    rows = []
    for arxiv_id in tqdm(dirs):
        result = compare_text_similarity.main(arxiv_id)
        result_as_row = { 'arxiv_id': arxiv_id }
        for e1, e2 in DIFF_ENGINE_PAIRS:
            res = { f'{e1}{e2}_{key}': val for key,val in result[f'{e1}{e2}'].to_dict().items() }
            result_as_row = result_as_row | res
        rows.append(result_as_row)
    LOGGER.info(f'logfile timestamp: {current_time}')
    RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='arxiv_id')
    LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
    RESULTS_SUMMARY.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_analysis_results.csv'))


def run(args):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    # set up logger depending on what the command is
    if args.count_pages:
        logger.init_logger(logger.ANALYSIS_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.INFO, has_file_handler=False)
        count_pdf_pages.main(should_save=args.save)
        return
    if args.compare is not None:
        if args.compare == COMPARE_ALL: run_compare_all(current_time)
        else: run_compare_one(args.compare, args.save, current_time)
    if args.count_compiled:
        count_compiled_pdfs.main(should_save=args.save)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run analysis scripts')
    parser.add_argument('-save', action='store_true', help="save results to a file")
    parser.add_argument('-count-pages', action='store_true', help="count the number of pages for ALL pdfs")
    parser.add_argument('-count-compiled', action='store_true', help="count the number compiled pdfs across all engines")
    parser.add_argument('-compare', nargs='?', default=None, const=COMPARE_ALL, help="arxiv_id to compare text")
    args = parser.parse_args()

    # leggooooooooooooooooo
    run(args)
