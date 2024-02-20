from typing import Dict

from pandas import DataFrame
from analysis import compare_text_similarity
from analysis.helpers import COMPARISON, init_df_with_cols
from analysis.text_transformer import COMMON_ACCENTS, IGNORE_HYPHENS, TextTransformer
from utils.logger import ANALYSIS_LOGGER as LOGGER, pad_with_char

def text_transformation(text: str):
    text = TextTransformer.apply_transform(text, [IGNORE_HYPHENS])
    text = TextTransformer.apply_transform(text, COMMON_ACCENTS)
    return text

def find_different_chars(edit_ops: Dict[str, DataFrame]):
    different_chars = {}
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
    return different_chars

def text_comparison(pdf_texts: Dict[str, str]):
    edit_ops_results = compare_text_similarity.compute_edit_ops(pdf_texts)
    cleaned_results, summary = compare_text_similarity.compute_cleaned_edit_ops(edit_ops_results)

    RESULTS = init_df_with_cols(['comparison', 'xepdf', 'xelua'], 'comparison')
    RESULTS = compare_text_similarity.compute_text_comparison_metrics(compare_text_similarity.COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compare_text_similarity.compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, summary, RESULTS)
    RESULTS = compare_text_similarity.compute_edit_ops_metrics(edit_ops_results, RESULTS)
    different_chars = find_different_chars(edit_ops_results)
    for k, v in different_chars.items(): print(k, '\n', v)

    for e1, e2 in COMPARISON:
        cmp = f'{e1}{e2}'
        LOGGER.debug(pad_with_char(cmp, '-'))
        if not cmp in edit_ops_results:
            if e1 not in pdf_texts: LOGGER.debug(f'{e1} not found')
            if e2 not in pdf_texts: LOGGER.debug(f'{e2} not found')
            continue
        if edit_ops_results[cmp].shape[0] == 0: 
            LOGGER.debug('\nno text diffs found')
            continue
        LOGGER.debug(f'raw edit ops:\n' + edit_ops_results[cmp].head(15).to_string())
        LOGGER.debug(f'>> cleaned edit ops [{cmp}] [{cleaned_results[cmp].shape[0]} rows]:\n' + cleaned_results[cmp].head(20).to_string())
        LOGGER.debug(summary[cmp])

    LOGGER.debug('text comparison summary:\n' + RESULTS.to_string())
    return RESULTS

