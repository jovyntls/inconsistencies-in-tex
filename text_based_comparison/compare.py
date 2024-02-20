from collections import namedtuple
from typing import Any, Counter, Dict, List, Set
from analysis import compare_text_similarity
from analysis.helpers import COMPARISON, init_df_with_cols
from analysis.text_transformer import COMMON_ACCENTS, IGNORE_HYPHENS, TextTransformer
from text_based_comparison.extract import FontInformation, ImageInfo
from utils.logger import ANALYSIS_LOGGER as LOGGER, pad_with_char

THRESHOLD = 0.01  # percentage difference allowed in image dimensions

def text_transformation(text: str):
    text = TextTransformer.apply_transform(text, [IGNORE_HYPHENS])
    text = TextTransformer.apply_transform(text, COMMON_ACCENTS)
    return text

def text_comparison(pdf_texts: Dict[str, str]):
    # pdf_infos: { pdflatex: ..., xelatex: ... }
    # pdf_texts: { pdf: ..., xe: ... }
    edit_ops_results = compare_text_similarity.compute_edit_ops(pdf_texts)
    analysed_edit_opts_results = compare_text_similarity.analyse_edit_opts_results(edit_ops_results)
    cleaned_results, summary = compare_text_similarity.compute_cleaned_edit_ops(edit_ops_results)
    RESULTS = init_df_with_cols(['comparison', 'xepdf', 'xelua'], 'comparison')
    RESULTS = compare_text_similarity.compute_text_comparison_metrics(compare_text_similarity.COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compare_text_similarity.compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, summary, RESULTS)
    RESULTS = compare_text_similarity.compute_edit_ops_metrics(edit_ops_results, RESULTS)

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
        LOGGER.debug(f'>> edit ops [{cmp}] [{edit_ops_results[cmp].shape[0]} rows]: summary\n' + analysed_edit_opts_results[cmp].to_string())
        LOGGER.debug(f'raw edit ops:\n' + edit_ops_results[cmp].head(15).to_string())
        LOGGER.debug(f'>> cleaned edit ops [{cmp}] [{cleaned_results[cmp].shape[0]} rows]:\n' + cleaned_results[cmp].head(20).to_string())
        LOGGER.debug(summary[cmp])

    LOGGER.debug('text comparison summary:\n' + RESULTS.to_string())
    return RESULTS

ImgCmpResult = namedtuple('ImgCmpResult', ['img_correct_order', 'img_num_missing', 'img_num_diff_size'])
def image_comparison(imgs1: List[ImageInfo], imgs2: List[ImageInfo]):
    # check order
    ordered_binaries1 = [img.digest for img in imgs1]
    ordered_binaries2 = [img.digest for img in imgs2]
    is_correct_order = ordered_binaries1 == ordered_binaries2
    # check missing images
    img_counts1 = Counter(ordered_binaries1)
    img_counts2 = Counter(ordered_binaries2)
    missing_images = (img_counts1 - img_counts2) | (img_counts2 - img_counts1)
    if len(missing_images) > 0: 
        LOGGER.debug('found {len(missing_images)} missing images')
        pass 
    # check image sizes
    img1_to_dims = {}
    diff_sized_imgs = []
    for img_info in imgs1:
        img, dim = img_info.digest, img_info.dimensions
        if img not in img1_to_dims: img1_to_dims[img] = []
        img1_to_dims[img].append(dim)
    for img_info in reversed(imgs2):
        img, dim2 = img_info.digest, img_info.dimensions
        if img not in img1_to_dims: continue
        w1, h1 = img1_to_dims[img].pop()
        w2, h2 = dim2
        min_w, max_w, min_h, max_h = min(w1, w2), max(w1, w2), min(h1, h2), max(h1, h2)
        if max_w/min_w > 1+THRESHOLD or max_h/min_h > 1+THRESHOLD: diff_sized_imgs.append(img)
    if len(diff_sized_imgs) > 0:
        LOGGER.debug('found {len(diff_sized_imgs)} different-sized images')
        pass
    return ImgCmpResult(is_correct_order, sum(missing_images.values()), len(diff_sized_imgs))

def run_img_comparison(pdf_imgs: Dict[str, List[ImageInfo]]):
    # result_rows_as_dict = { fieldname: { xepdf: 0, xelua: 1 } }
    result_rows_as_dict = { field: {} for field in ImgCmpResult._fields }
    for e1, e2 in COMPARISON:
        if e1 not in pdf_imgs or e2 not in pdf_imgs: continue
        col = f'{e1}{e2}'
        cmp_result = image_comparison(pdf_imgs[e1], pdf_imgs[e2])
        for fieldname in cmp_result._fields:
            result_rows_as_dict[fieldname][col] = getattr(cmp_result, fieldname)
    result_rows = [ field_result | { 'comparison': fieldname } for fieldname, field_result in result_rows_as_dict.items() ]
    return result_rows

def run_font_comparison(pdf_fonts: Dict[str, Set[FontInformation]]):
    num_fonts: Dict[str, Any] = { 'comparison': 'fonts_num' }
    for e1, e2 in COMPARISON: 
        if e1 not in pdf_fonts or e2 not in pdf_fonts: continue
        col = f'{e1}{e2}'
        num_fonts[col] = abs(len(pdf_fonts[e1]) - len(pdf_fonts[e2]))
    return [num_fonts]

