import argparse
import logging
import os
from datetime import datetime
import warnings
from tqdm import tqdm
import pandas as pd
import img_comparison.compare_text as text_cmp

from utils import logger
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from img_comparison import convert_pdf_to_img, compare_imgs
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS

LOGGER = logger.COMPARISON_LOGGER

def convert_for_all():
    LOGGER.info('converting PDFs to image...')
    for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER)):
        convert_pdf_to_img.main(arxiv_id)

def compare_for_all(algos):
    dirs = os.listdir(COMPILED_FOLDER)
    rows = []
    LOGGER.info('running image comparisons...')
    for arxiv_id in tqdm(dirs):
        result = compare_imgs.main(arxiv_id, algos)
        for page, page_results in result.items():
            page_results['identifier'] = f'{arxiv_id}_{page}'
            rows.append(page_results)
    RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='identifier')
    LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
    return RESULTS_SUMMARY

def pretty_print_results(results_df, arxiv_id):
    LOGGER.info(f'text comparison results for {arxiv_id=}:')
    col_keys = [ f'{e1}{e2}' for e1, e2 in DIFF_ENGINE_PAIRS ]
    replacements = [ ('normalised', 'norm'), ('hamming', 'HM'), ('levenshtein', 'LV') ] + [ (col+'_', '') for col in col_keys ]
    for col_key in col_keys:
        cmp_data = pd.DataFrame()
        for colname in results_df.columns:
            if col_key not in colname: continue
            new_colname = colname
            for before, after in replacements: new_colname = new_colname.replace(before, after)
            cmp_data[new_colname] = results_df[colname]
        LOGGER.info(f'{col_key}:\n{cmp_data}')

def run(run_for_id, do_convert, do_compare, do_text):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if run_for_id is None: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.INFO, has_file_handler=True)
        warnings.filterwarnings('ignore')
        LOGGER.info(f'logfile timestamp: {current_time}')
        LOGGER.info(f'{do_convert=}\t{do_compare=}\t{do_text=}')
        if do_convert: convert_for_all()
        if do_compare: 
            results = compare_for_all(algos=do_compare)
            results.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_imgcompare.csv'))
        if do_text:
            results = text_cmp.run_text_cmp_for_all()
            results.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_textcompare.csv'))
    else: 
        logger.init_logger(logger.COMPARISON_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.DEBUG, has_file_handler=False)
        arxiv_id = f'{YEAR_AND_MONTH}.{run_for_id}'
        if do_convert: convert_pdf_to_img.main(arxiv_id)
        if do_compare: compare_imgs.main(arxiv_id, algos=do_compare)
        if do_text: 
            result = text_cmp.run_text_cmp(arxiv_id)
            results_as_df = pd.DataFrame.from_records(result, index='identifier')
            pretty_print_results(results_as_df, arxiv_id)

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run image comparison')
    parser.add_argument('-id', nargs='?', default=None, help="arxiv_id to run on (runs on all PDFs if not specified)")
    parser.add_argument('-convert', action='store_true', help="run conversion (of pdf to img) only")
    parser.add_argument('-compare', action='store_true', help="run image comparison only")
    cmp_choices = list(compare_imgs.CMP_ALGORITHMS.keys())
    parser.add_argument('-cmpalgo', action='append', choices=cmp_choices, default=[], help="run image comparison with a specific algorithm")
    parser.add_argument('-text', action='store_true', help="run text comparison only")
    args = parser.parse_args()

    do_all = not args.compare and not args.convert and not args.text
    do_compare = (args.compare or do_all) and (args.cmpalgo or cmp_choices)
    do_convert = args.convert or do_all
    do_text = args.text or do_all
    run(args.id, do_convert, do_compare, do_text)
