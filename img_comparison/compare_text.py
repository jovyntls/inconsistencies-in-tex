import os
import fitz
from tqdm import tqdm
import pandas as pd
from analysis.compare_text_similarity import COMPARE_METHODS, compute_cleaned_edit_ops, compute_edit_ops, compute_edit_ops_metrics, compute_levenshtein_cleaned_and_edit_ops_summary, compute_text_comparison_metrics
from img_comparison.convert_pdf_to_img import get_pages_to_convert
from utils.logger import COMPARISON_LOGGER as LOGGER
import analysis.text_transformer as Ttr
from config import COMPILED_FOLDER
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS, TEX_ENGINES, get_engine_name

DEFAULT_TRANSFORMER = Ttr.transformer_ignore_hyphenbreak_pagebreak_linebreak

def get_text_from_page(pdf_doc, page_num):
    page = pdf_doc[page_num]
    processed_text = DEFAULT_TRANSFORMER.process([page.get_text()])
    return processed_text

# returns a nested dictionary of pagenum -> engine -> text
def collect_text_to_compare(arxiv_id):
    texts = {}
    for engine in TEX_ENGINES:
        pdf_filepath = os.path.join(COMPILED_FOLDER, arxiv_id, f'{arxiv_id}_{get_engine_name(engine)}.pdf')
        if not os.path.exists(pdf_filepath):
            LOGGER.debug(f'{pdf_filepath} not found - skipping')
            continue
        try:
            doc = fitz.open(pdf_filepath)
        except Exception as err:
            LOGGER.warn(f'skipping textcompare due to error opening file {pdf_filepath}:\n{err}')
            continue
        pages_to_compare = get_pages_to_convert(doc)
        for page_num, cmp_idx in pages_to_compare:
            page_text = get_text_from_page(doc, page_num)
            if cmp_idx not in texts: texts[cmp_idx] = {}
            texts[cmp_idx][engine] = page_text
    return texts

# @param [cmp_group] is a dictionary of engine -> text
# @param [identifier] is 2306.12345_cmp-2
def run_cross_engine_comparison(cmp_group, identifier):
    edit_ops_results = compute_edit_ops(cmp_group)
    cleaned_results, summary = compute_cleaned_edit_ops(edit_ops_results)

    results = pd.DataFrame(columns=[identifier] + [f'{e1}{e2}' for e1, e2 in DIFF_ENGINE_PAIRS]).set_index(identifier)
    results = compute_text_comparison_metrics(COMPARE_METHODS, cmp_group, results)
    results = compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, summary, results)
    results = compute_edit_ops_metrics(edit_ops_results, results)
    return results

# convert the result of a single comparison (one page across different engines) to a row
def convert_cmp_result_to_row(result, identifier):
    result_as_row = { 'identifier': identifier }
    for e1, e2 in DIFF_ENGINE_PAIRS:
        res = { f'{e1}{e2}_{key}': val for key,val in result[f'{e1}{e2}'].to_dict().items() }
        result_as_row = result_as_row | res
    return result_as_row

# run text comparison for a single arxiv id
def run_text_cmp(arxiv_id):  # arxiv_id including YYMM
    img_subdir = os.path.join(COMPILED_FOLDER, arxiv_id)
    if not os.path.exists(img_subdir): 
        LOGGER.warn(f'can\'t find compiled PDf folder for {arxiv_id}')
        return
    RESULT_ROWS = []
    texts = collect_text_to_compare(arxiv_id)
    for cmp_page_num, cmp_group in texts.items():
        identifier = f'{arxiv_id}_cmp{cmp_page_num}'
        page_result = run_cross_engine_comparison(cmp_group, identifier)
        page_result_as_row = convert_cmp_result_to_row(page_result, identifier)
        RESULT_ROWS.append(page_result_as_row)
    return RESULT_ROWS

def run_text_cmp_for_all():
    RESULT_ROWS = []
    dirs = os.listdir(COMPILED_FOLDER)
    for arxiv_id in tqdm(dirs):
        single_doc_results = run_text_cmp(arxiv_id)
        if single_doc_results is None: continue
        RESULT_ROWS += single_doc_results
    RESULTS_AS_DF = pd.DataFrame.from_records(RESULT_ROWS, index='identifier')
    return RESULTS_AS_DF

