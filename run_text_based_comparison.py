import argparse
import logging
import os
from datetime import datetime
import warnings
from tqdm import tqdm
import pandas as pd
from analysis.helpers import COMPARISON

from utils import logger, tex_engine_utils
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from text_based_comparison import extract, compare

LOGGER = logger.COMPARISON_LOGGER

def compare_for_one(arxiv_id, should_save):
    pdf_infos = {}
    for engine in tex_engine_utils.TEX_ENGINES:
        pdf_filepath = os.path.join(COMPILED_FOLDER, arxiv_id, f'{arxiv_id}_{engine}.pdf')
        if not os.path.isfile(pdf_filepath): continue
        pdf_infos[engine] = extract.get_text_fonts_images(pdf_filepath)
    # pdf_infos: { pdflatex: ..., xelatex: ... }
    # pdf_texts: { pdf: ..., xe: ... }
    pdf_texts = { k[:-5]: compare.text_transformation(content.text) for k, content in pdf_infos.items() }

    # save if needed
    if should_save:
        for engine, text in pdf_texts.items():
            with open(f'text_{engine}.txt', 'w') as file: file.write(text)

    text_cmp_results = compare.text_comparison(pdf_texts)
    return pdf_infos

def compare_for_all():
    rows = []
    LOGGER.info('running text/format/image comparisons...')
    for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER)):
        pdf_infos = compare_for_one(arxiv_id, False)
        # for page, page_results in result.items():
        #     page_results['identifier'] = f'{arxiv_id}_{page}'
        #     rows.append(page_results)
    # RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='identifier')
    # LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
    # return RESULTS_SUMMARY


def run(run_for_id, should_save):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if run_for_id is None: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.INFO, has_file_handler=True)
        warnings.filterwarnings('ignore')
        LOGGER.info(f'logfile timestamp: {current_time}')
        LOGGER.info(f'{should_save=}')
        compare_for_all()
    else: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.DEBUG, has_file_handler=False)
        while len(run_for_id) < 5: run_for_id = '0' + run_for_id
        arxiv_id = f'{YEAR_AND_MONTH}.{run_for_id}'
        compare_for_one(arxiv_id, should_save)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run text-based comparison (text, formatting, images)')
    parser.add_argument('-id', nargs='?', default=None, help="arxiv_id to run on (runs on all PDFs if not specified)")
    parser.add_argument('-save', action='store_true', help="save the text outputs to tmp{1,2,3}.txt for running diffs")
    args = parser.parse_args()

    run(args.id, args.save)
