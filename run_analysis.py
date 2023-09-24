import argparse
import os
from datetime import datetime

from utils import logger
from config import LOGS_FOLDER
from analysis import count_pdf_pages, compare_text_similarity

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run analysis scripts')
    parser.add_argument('-save', action='store_true', help="save results to a file")
    parser.add_argument('-count', action='store_true', help="count the number of pages for ALL pdfs")
    parser.add_argument('-compare', type=str, help="arxiv_id to compare text")
    args = parser.parse_args()

    # set up logger
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    logger.init_for_pipeline(LOGS_FOLDER, current_time)

    # run things
    if args.count:
        count_pdf_pages.main(should_save=args.save)
    if args.compare:
        compare_text_similarity.main(args.compare)
        if args.save:
            compare_text_similarity.extract_pdf_text_to_save_file(args.compare)
