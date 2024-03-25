from typing import Any, Dict

import pandas as pd
from analysis import compare_text_similarity
from analysis.helpers import init_df_with_cols
from analysis.text_transformer import COMMON_ACCENTS, IGNORE_HYPHENS, TextTransformer
from text_based_comparison.extract import PdfContent
from utils.logger import ANALYSIS_LOGGER as LOGGER, pad_with_char
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS

def text_transformation(text: str):
    text = TextTransformer.apply_transform(text, [IGNORE_HYPHENS])
    text = TextTransformer.apply_transform(text, COMMON_ACCENTS)
    text = TextTransformer.apply_transform(text, [ ('ϕ', ''), ('φ', '') ])
    return text

def find_different_chars(edit_ops: Dict[str, pd.DataFrame]):
    different_chars: Dict[str, Dict[str, int]] = {}  # { [cmp]: { [char]: [count] }
    different_chars_count: Dict[str, Any] = { 'comparison': 'chars_diff_nett' }
    different_chars_count_uniq: Dict[str, Any] = { 'comparison': 'chars_diff_uniq' }
    for cmp, edit_ops_df in edit_ops.items():
        char_counts = {}
        for _, row in edit_ops_df.iterrows():
            from_char, to_char, char_count = row['from'], row['to'], row['count']
            if from_char not in char_counts: char_counts[from_char] = 0
            if to_char not in char_counts: char_counts[to_char] = 0
            char_counts[from_char] -= char_count
            char_counts[to_char] += char_count
        # [from] or [to] may be blank (== '') if it's not a replace op, so delete all '' keys
        if '' in char_counts: char_counts.pop('')
        different_chars[cmp] = { k:v for k, v in char_counts.items() if v != 0 and not k.isspace() }
        different_chars_count[cmp] = sum(different_chars[cmp].values())
        different_chars_count_uniq[cmp] = len(different_chars[cmp].keys())
    return different_chars, [ different_chars_count, different_chars_count_uniq ]

def text_comparison(pdf_texts: Dict[str, str], with_debug_info=False):
    edit_ops_results = compare_text_similarity.compute_edit_ops(pdf_texts)
    cleaned_results, summary = compare_text_similarity.compute_cleaned_edit_ops(edit_ops_results)
    different_chars, different_chars_summary_rows = find_different_chars(edit_ops_results)

    RESULTS = init_df_with_cols(['comparison'] + [f'{e1}{e2}' for e1, e2 in DIFF_ENGINE_PAIRS], 'comparison')
    RESULTS = compare_text_similarity.compute_text_comparison_metrics(compare_text_similarity.COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compare_text_similarity.compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, summary, RESULTS)
    RESULTS = compare_text_similarity.compute_edit_ops_metrics(edit_ops_results, RESULTS)
    RESULTS = pd.concat([RESULTS, pd.DataFrame.from_records(different_chars_summary_rows, index='comparison')])
    
    grouped_edit_ops = compare_text_similarity.compute_debug_edit_ops(pdf_texts) if with_debug_info else None

    for e1, e2 in DIFF_ENGINE_PAIRS:
        cmp = f'{e1}{e2}'
        LOGGER.debug(pad_with_char(cmp, '-'))
        if not cmp in edit_ops_results:
            if e1 not in pdf_texts: LOGGER.debug(f'{e1} not found')
            if e2 not in pdf_texts: LOGGER.debug(f'{e2} not found')
            continue
        if edit_ops_results[cmp].shape[0] == 0: 
            LOGGER.debug('\nno text diffs found')
            continue
        LOGGER.debug(f'>> cleaned edit ops [{cmp}] [{cleaned_results[cmp].shape[0]} rows]: {summary[cmp]}\n' + cleaned_results[cmp].head(20).to_string())
        # print the diff chars
        sorted_counts = sorted(different_chars[cmp].items(), key=lambda x: -abs(x[1]))
        LOGGER.debug('>> different characters:\n' + '\t'.join([ f'|  {k}: {v} ' for k, v in sorted_counts ]))

    LOGGER.debug('text comparison summary:\n' + RESULTS.to_string())
    return RESULTS, grouped_edit_ops

def num_pages_comparison(pdf_infos: Dict[str, PdfContent]):
    num_pages: Dict[str, Any] = { 'comparison': 'num_pages' }
    for e1, e2 in DIFF_ENGINE_PAIRS: 
        if e1 not in pdf_infos or e2 not in pdf_infos: continue
        col = f'{e1}{e2}'
        num_pages[col] = pdf_infos[e1].num_pages - pdf_infos[e2].num_pages
    return [num_pages]

