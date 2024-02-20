import argparse
import logging
import os
from datetime import datetime
import warnings
from tqdm import tqdm
import pandas as pd

from utils import logger, tex_engine_utils
from config import YEAR_AND_MONTH, LOGS_FOLDER, COMPILED_FOLDER
from text_based_comparison import extract, compare

# only include these in the final result summary (not applicable to single arxiv_id run)
TEXT_COMPARE_METRICS = ['levenshtein', 'levenshtein_normalised', 'levenshtein_cleaned', 'levenshtein_cleaned_normalised', 
                        'op_uppercase', 'op_lowercase', 'insert_minus_delete', 'img_correct_order', 'img_num_missing', 
                        'img_num_diff_size', 'fonts_num']

LOGGER = logger.ANALYSIS_LOGGER

def compare_for_one(arxiv_id, should_save, should_save_debug):
    LOGGER.debug(f'{arxiv_id=}')
    pdf_infos = {}
    for engine in tex_engine_utils.TEX_ENGINES:
        pdf_filepath = os.path.join(COMPILED_FOLDER, arxiv_id, f'{arxiv_id}_{engine}.pdf')
        if not os.path.isfile(pdf_filepath): continue
        pdf_infos[engine], debug_content = extract.get_text_fonts_images(pdf_filepath)
        # save if needed
        if should_save_debug:
            with open(f'text_{engine}.txt', 'w') as file: file.write('\n'.join([ str(x) for x in debug_content ]))
        elif should_save:
            with open(f'text_{engine}.txt', 'w') as file: file.write(pdf_infos[engine].text)

    # pdf_infos: { pdflatex: ..., xelatex: ... }
    # pdf_texts, pdf_imgs: { pdf: ..., xe: ... }
    pdf_texts = { k[:-5]: compare.text_transformation(content.text) for k, content in pdf_infos.items() }
    pdf_imgs = { k[:-5]: content.images for k, content in pdf_infos.items() }
    pdf_fonts = { k[:-5]: content.fonts for k, content in pdf_infos.items() }

    RESULTS = compare.text_comparison(pdf_texts)
    img_cmp_results = compare.run_img_comparison(pdf_imgs)
    font_cmp_results = compare.run_font_comparison(pdf_fonts)
    RESULTS = pd.concat([RESULTS, pd.DataFrame.from_records(img_cmp_results + font_cmp_results, index='comparison')])
    return RESULTS

def compare_for_all(is_debug_run):
    rows = []
    LOGGER.info('running text/format/image comparisons...')
    dirs = os.listdir(COMPILED_FOLDER)[:20] if is_debug_run else os.listdir(COMPILED_FOLDER)
    for arxiv_id in tqdm(dirs):
        result = compare_for_one(arxiv_id, False, False)
        xelua_result = { f'xelua_{key}': val for key,val in result['xelua'].to_dict().items() if key in TEXT_COMPARE_METRICS }
        xepdf_result = { f'xepdf_{key}': val for key,val in result['xepdf'].to_dict().items() if key in TEXT_COMPARE_METRICS }
        result_as_row = { 'arxiv_id': arxiv_id } | xelua_result | xepdf_result
        rows.append(result_as_row)
    RESULTS_SUMMARY = pd.DataFrame.from_records(rows, index='arxiv_id')
    return RESULTS_SUMMARY

def run(run_for_id, should_save, debug_mode):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    if run_for_id is None: 
        logger.init_logger(logger.ANALYSIS_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.INFO, has_file_handler=True)
        warnings.filterwarnings('ignore')
        LOGGER.info(f'logfile timestamp: {current_time}')
        LOGGER.info(f'{should_save=}')

        RESULTS_SUMMARY = compare_for_all(debug_mode)

        LOGGER.debug('full results summary:\n' + RESULTS_SUMMARY.to_string())
        RESULTS_SUMMARY.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_analysis_results.csv'))
    else: 
        logger.init_logger(logger.ANALYSIS_LOGGER_ID, LOGS_FOLDER, current_time,
                           console_log_level=logging.DEBUG, has_file_handler=False)
        while len(run_for_id) < 5: run_for_id = '0' + run_for_id
        arxiv_id = f'{YEAR_AND_MONTH}.{run_for_id}'
        RESULT = compare_for_one(arxiv_id, should_save, debug_mode)
        LOGGER.info(f'[arxiv_id={arxiv_id}] RESULT:\n' + RESULT.to_string())

if __name__ == '__main__':
    # set up CLI args
    parser = argparse.ArgumentParser(description='Run text-based comparison (text, formatting, images)')
    parser.add_argument('-id', nargs='?', default=None, help="arxiv_id to run on (runs on all PDFs if not specified)")
    parser.add_argument('-save', action='store_true', help="save the text outputs to text_{pdf,xe,lua}.txt for running diffs")
    parser.add_argument('-debug', action='store_true', help="for single run, save the text output with font information for debugging (overrides -save). for full run, only run for 20 files")
    args = parser.parse_args()

    run(args.id, args.save, args.debug)
