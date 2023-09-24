import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from analysis import count_pdf_pages, compare_text_similarity

COMPARE_ALL = 'COMPARE_ALL'
LOGGER = logger.ANALYSIS_LOGGER

def run(args):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    # set up logger depending on what the command is
    if args.count:
        logger.init_for_analysis(LOGS_FOLDER, current_time, has_file_handler=False)
        count_pdf_pages.main(should_save=args.save)
        return
    if args.compare is not None:
        # only log to a file if running for all
        is_compare_all = args.compare == COMPARE_ALL
        console_log_level = logging.INFO if is_compare_all else logging.DEBUG
        logger.init_for_analysis(LOGS_FOLDER, current_time, has_file_handler=is_compare_all, console_log_level=console_log_level)

        if is_compare_all:
            dirs = os.listdir(COMPILED_FOLDER)
            rows = []
            for arxiv_id in tqdm(dirs):
                result = compare_text_similarity.main(arxiv_id)
                xelua_result = { f'xelua_{key}': val for key,val in result['xelua'].to_dict().items() }
                xepdf_result = { f'xepdf_{key}': val for key,val in result['xepdf'].to_dict().items() }
                result_as_row = { 'arxiv_id': arxiv_id } | xelua_result | xepdf_result
                rows.append(result_as_row)
            LOGGER.info(f'logfile timestamp: {current_time}')
            RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='arxiv_id')
            LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
            RESULTS_SUMMARY.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_analysis_results.csv'))
        else:
            arxiv_id = f'{YEAR_AND_MONTH}.{args.compare}'
            compare_text_similarity.main(arxiv_id)
            if args.save:
                compare_text_similarity.extract_pdf_text_to_save_file(arxiv_id)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run analysis scripts')
    parser.add_argument('-save', action='store_true', help="save results to a file")
    parser.add_argument('-count', action='store_true', help="count the number of pages for ALL pdfs")
    parser.add_argument('-compare', nargs='?', default=None, const=COMPARE_ALL, help="arxiv_id to compare text")
    args = parser.parse_args()

    # leggooooooooooooooooo
    run(args)
