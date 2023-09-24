import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from analysis import count_pdf_pages, compare_text_similarity

COMPARE_ALL = 'COMPARE_ALL'

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
            for arxiv_id in tqdm(dirs):
                compare_text_similarity.main(arxiv_id)
            logger.ANALYSIS_LOGGER.info(f'logfile timestamp: {current_time}')
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
