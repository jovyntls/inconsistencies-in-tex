import os
import fitz  # imports the pymupdf library
import Levenshtein
import pandas as pd
from typing import Dict, Any

from pandas.core.api import DataFrame

from config import COMPILED_FOLDER
from utils.logger import ANALYSIS_LOGGER as LOGGER, pad_with_char
import analysis.helpers as helpers
import analysis.text_transformer as Ttr
from utils.tex_engine_utils import get_engine_name, TEX_ENGINES as ENGINES, DIFF_ENGINE_PAIRS as COMPARISON

DF_COMPARISON_INDEX = 'comparison'

# < PDF to string helpers > ---------------------------------------------------

def extract_pages_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text() for page in doc]
        images = [page.get_image_info(hashes=True) for page in doc]
        return pages, images
    except:
        return None, None

def extract_pages_and_images_from_pdfs(COMPILED_FOLDER, arxiv_id):
    compiled_pdfs_dir = os.path.join(COMPILED_FOLDER, arxiv_id)
    pdf_texts = {}
    pdf_images = {}
    for engine in ENGINES:
        pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{get_engine_name(engine)}.pdf')
        pages, images = extract_pages_from_pdf(pdf_path)
        if pages != None: pdf_texts[engine] = pages
        if images != None: pdf_images[engine] = images
    return pdf_texts, pdf_images

def process_pages_to_string(engine_to_pages, transformer):
    pdf_texts = {}
    for engine, pages in engine_to_pages.items():
        if pages == None: continue
        pdf_texts[engine] = transformer.process(pages)
    return pdf_texts

def process_image_info(img_info):
    # get top-left corner position, dimensions, size
    x1, y1, x2, y2 = img_info['bbox']
    width, height = x2-x1, y2-y1
    info = {
        'img_id': img_info['digest'],
        'pos': (x1, y1),
        'aspect_ratio': 0 if height == 0 else width/height,
        'width': width,
        'height': height
    }
    return info

# </ PDF to string helpers > --------------------------------------------------

# < text comparison helpers > -------------------------------------------------

def compare_texts_with_method(pdf_texts, compare_f):
    result = {}
    for e1, e2 in COMPARISON:
        if e1 not in pdf_texts or e2 not in pdf_texts: continue
        text1, text2 = pdf_texts[e1], pdf_texts[e2]
        result[f'{e1}{e2}'] = compare_f(text1, text2)
    return result

def normalise(f):
    def compare(text1, text2):
        score = f(text1, text2)
        max_length = max(len(text1), len(text2))
        if max_length == 0: return 1
        normalised_score = 1 - (score / max_length)
        return normalised_score
    return compare

def cmp_with_threshold(v1, v2, threshold=5):
    diff = abs(v1 - v2)
    return diff < threshold

def cmp_img_info(info1, info2):
    pos_identical = cmp_with_threshold(info1['pos'][0], info2['pos'][0]) and cmp_with_threshold(info1['pos'][1], info2['pos'][1])
    if not pos_identical: 
        LOGGER.debug(f'diffs in comparing img: [pos_identical]\n\t{info1}\n\t{info2}')
        return False
    cmp_attributes = [ 'aspect_ratio', 'width', 'height' ]
    for attrib in cmp_attributes:
        identical = cmp_with_threshold(info1[attrib], info2[attrib])
        if not identical: 
            LOGGER.debug(f'diffs in comparing img: [{attrib}]\t{info1[attrib]}\t{info2[attrib]}\n\t{info1}\n\t{info2}')
            return False
    return True

def compare_all_img_infos(l1, l2):
    if len(l1) != len(l2): 
        LOGGER.debug(f'different number of images: {len(l1)}, {len(l2)}')
        return False
    for img_id in l1.keys():
        if img_id not in l2: 
            LOGGER.debug(f'missing image_id: {img_id=}')
            return False
        if not cmp_img_info(l1[img_id], l2[img_id]): return False
    return True


# </ text comparion helpers > -------------------------------------------------

# < edit_op helpers > ---------------------------------------------------------

def transform_op(edit_op, s1, s2):
    action, src_index, dest_index = edit_op
    match action:
        case 'insert':
            return (action, src_index, dest_index, '', s2[dest_index])
        case 'delete':
            return (action, src_index, dest_index, s1[src_index], '')
        case 'replace':
            return (action, src_index, dest_index, s1[src_index], s2[dest_index])
        case 'equal':
            return None
        case _:
            LOGGER.warn(f'unknown op: {action}')
            return None

def get_edit_ops(text1, text2):
    ops = Levenshtein.editops(text1, text2)
    transformed_ops = [transform_op(op, text1, text2) for op in ops]
    return [x for x in transformed_ops if x is not None]

def collate_edit_ops(edit_ops):
    collated = {}
    for action, _, _, src_char, dest_char in edit_ops:
        op_index = (action, src_char, dest_char)
        if op_index not in collated: collated[op_index] = 0
        collated[op_index] += 1
    return collated

def group_edit_ops(edit_ops):
    def new_edit_group():
        return { 'insert': [], 'delete': [], 'replace': [] }
    def add_to_edit_group(grp, action, src, dest):
        match action:
            case 'insert': grp[action].append(dest)
            case 'delete': grp[action].append(src)
            case 'replace': grp[action].append((src, dest))
        return
    src_edits_grouped, dest_edits_grouped = {}, {}
    src_curr_loc, dest_curr_loc = (-100,-100), (-100,-100)
    src_curr_group, dest_curr_group = new_edit_group(), new_edit_group()
    # count the edit locations for debugging purposes
    for action, src_idx, dest_idx, src_char, dest_char in edit_ops:
        # src part
        if src_idx <= src_curr_loc[-1]: 
            src_curr_loc = (src_curr_loc[0], src_idx+1)
        else: 
            src_edits_grouped[src_curr_loc] = src_curr_group
            src_curr_loc, src_curr_group  = (src_idx, src_idx+1), new_edit_group()
        add_to_edit_group(src_curr_group, action, src_char, dest_char)
        # dest part
        if dest_idx <= dest_curr_loc[-1]: 
            dest_curr_loc = (dest_curr_loc[0], dest_idx+1)
        else: 
            dest_edits_grouped[dest_curr_loc] = dest_curr_group
            dest_curr_loc, dest_curr_group  = (dest_idx, dest_idx+1), new_edit_group()
        add_to_edit_group(dest_curr_group, action, src_char, dest_char)
    src_edits_grouped[src_curr_loc], dest_edits_grouped[dest_curr_loc] = src_curr_group, dest_curr_group
    src_edits_grouped.pop((-100,-100))
    dest_edits_grouped.pop((-100,-100))
    return src_edits_grouped, dest_edits_grouped

def analyse_edit_opts_results(edit_ops_results):
    RESULTS = {}
    for cmp_engines, df in edit_ops_results.items():
        grouped = df.groupby('action')['count'].sum().reset_index()
        RESULTS[cmp_engines] = grouped
    return RESULTS

def characterise_common_edit_op(action, old_c, new_c):
    # spaces
    if old_c.strip() == new_c.strip() == '': return 'whitespace'
    # (un)capitalisation: upper->lower, lower->upper
    if action == 'replace' and old_c.lower() == new_c.lower():
        if old_c == old_c.lower(): return 'lower-upper'
        else: return 'upper-lower'
    return None

def clean_edit_ops_results(edit_ops_results):
    """clean out changes in whitespace, upper/lower case, simple movements"""
    def find_corresponding_delete_index(char, deletions_df):
        matching_indexes = deletions_df.index[deletions_df['from'] == char]
        if len(matching_indexes) == 0: return None
        assert len(matching_indexes) == 1
        return matching_indexes[0]

    summary = { 'whitespace': 0, 'lower-upper': 0, 'upper-lower': 0, 'movements': 0 }
    indexes_to_keep = []
    # create a new df without the common trivial edit ops
    for index, row in edit_ops_results.iterrows():
        type_of_edit_op = characterise_common_edit_op(row['action'], row['from'], row['to'])
        if type_of_edit_op is not None: summary[type_of_edit_op] += 1
        else: indexes_to_keep.append(index)
    cleaned_results = edit_ops_results.loc[indexes_to_keep]
    # remove simple movements from the new df
    insertions, deletions = cleaned_results[cleaned_results['action'] == 'insert'], cleaned_results[cleaned_results['action'] == 'delete']
    for index, row in insertions.iterrows():
        corresponding_delete_index = find_corresponding_delete_index(row['to'], deletions)
        if corresponding_delete_index is None: continue
        delete_count = cleaned_results.loc[corresponding_delete_index, 'count']
        num_movements = min(row['count'], delete_count)
        cleaned_results.loc[index, 'count'] -= num_movements
        cleaned_results.loc[corresponding_delete_index, 'count'] -= num_movements
        summary['movements'] += num_movements
    cleaned_results = cleaned_results.loc[cleaned_results['count'] > 0]
    return cleaned_results, summary

# </ edit_op helpers > --------------------------------------------------------

# < runners > -----------------------------------------------------------------

def compute_edit_ops(pdf_texts):
    """Compute Levenshtein edit ops (insert/delete/replace)"""
    def compute_edit_ops_for_engine(e1, e2):
        edit_ops = get_edit_ops(pdf_texts[e1], pdf_texts[e2])
        collated_ops = collate_edit_ops(edit_ops)
        data = [ ( *op, counts ) for op, counts in collated_ops.items() ]
        df = pd.DataFrame(data, columns=pd.Index(['action', 'from', 'to', 'count']))
        return df.sort_values(by=['count'], ascending=False)
    RESULTS = {}
    for e1, e2 in COMPARISON:
        if e1 not in pdf_texts or e2 not in pdf_texts: continue
        RESULTS[f'{e1}{e2}']  = compute_edit_ops_for_engine(e1, e2)
    return RESULTS

def compute_debug_edit_ops(pdf_texts):
    EDIT_OPS_DEBUG = {}
    for e1, e2 in COMPARISON:
        if e1 not in pdf_texts or e2 not in pdf_texts: continue
        edit_ops = get_edit_ops(pdf_texts[e1], pdf_texts[e2])
        debug_ops_e1, debug_ops_e2 = group_edit_ops(edit_ops)
        EDIT_OPS_DEBUG[f'{e1}{e2}'] = { f'{e1}': debug_ops_e1, f'{e2}': debug_ops_e2 }
    return EDIT_OPS_DEBUG

def compute_cleaned_edit_ops(edit_ops_results):
    """For all engines, filter out changes in whitespace, upper/lower case, simple movements"""
    cleaned_results: Dict[str, DataFrame] = {}
    summary: Dict[str, Dict[str, int]] = {}
    for e1, e2 in COMPARISON:
        cmp = f'{e1}{e2}'
        if cmp not in edit_ops_results: continue
        cleaned_ops, summary[cmp] = clean_edit_ops_results(edit_ops_results[cmp])
        cleaned_results[cmp] = cleaned_ops.sort_values(by=['count'], ascending=False)
    return cleaned_results, summary

def compute_text_comparison_metrics(COMPARE_METHODS, pdf_texts, df):
    RESULTS = []
    for method_name, f in COMPARE_METHODS.items():
        row = compare_texts_with_method(pdf_texts, f)
        row[DF_COMPARISON_INDEX] = method_name
        RESULTS.append(row)
    # save compare text results to a df
    df = pd.concat([df, pd.DataFrame.from_records(RESULTS, index=DF_COMPARISON_INDEX)])
    return df

def compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, edit_summary, df):
    levenshtein_cleaned_row = { cmp: cleaned_edit_ops['count'].sum() for cmp, cleaned_edit_ops in cleaned_results.items() }
    levenshtein_cleaned_normalised_row = {}
    for cmp, cleaned_count in levenshtein_cleaned_row.items():
        try: 
            levenshtein_value = df.loc['levenshtein', cmp]
            if levenshtein_value == 0: 
                levenshtein_cleaned_normalised_row[cmp] = 1
                continue
            levenshtein_normalised_value = df.loc['levenshtein_normalised', cmp]
            levenshtein_cleaned_normalised_row[cmp] = (1-cleaned_count/levenshtein_value * (1-levenshtein_normalised_value))
        except KeyError:
            continue
    levenshtein_cleaned_row[DF_COMPARISON_INDEX] = 'levenshtein_cleaned'
    levenshtein_cleaned_normalised_row[DF_COMPARISON_INDEX] = 'levenshtein_cleaned_normalised'
    # add summary edit ops
    summary_attribs = { 'op_uppercase': 'lower-upper', 'op_lowercase': 'upper-lower', 'op_movement': 'movements', 'op_whitespace': 'whitespace' }
    summary_rows = []
    for cmp_name, attrib_name in summary_attribs.items():
        row = { f'{e1}{e2}' : edit_summary[f'{e1}{e2}'][attrib_name] for e1,e2 in COMPARISON if f'{e1}{e2}' in edit_summary }
        row[DF_COMPARISON_INDEX] = cmp_name
        summary_rows.append(row)
    df = pd.concat([df, pd.DataFrame.from_records([levenshtein_cleaned_row, levenshtein_cleaned_normalised_row] + summary_rows, index=DF_COMPARISON_INDEX)])
    return df

def compute_image_comparison_metrics(pdf_images, df):
    # compute the counts
    num_imgs = { engine: sum([len(imgs_in_pg) for imgs_in_pg in imgs]) for engine, imgs in pdf_images.items() }
    img_placements = { engine: [] for engine in pdf_images.keys() }
    img_infos = {}
    for engine, imgs_by_page in pdf_images.items():
        img_info_flatlist = [item for row in pdf_images[engine] for item in row]
        img_infos[engine] = { img_info['digest']: process_image_info(img_info) for img_info in img_info_flatlist }
        for page_index, imgs_in_page in enumerate(imgs_by_page):
            img_placements[engine] += [ (page_index + 1, img['digest']) for img in imgs_in_page ]
    # compute the comparisons
    img_placements_comparison_row : Dict[str, Any] = { 'comparison': 'img_placements' }
    num_imgs_comparison_row : Dict[str, Any] = { 'comparison': 'num_images' }
    img_info_comparison_row : Dict[str, Any] = { 'comparison': 'img_info' }
    for e1, e2 in COMPARISON:
        if e1 not in pdf_images or e2 not in pdf_images: continue
        col = f'{e1}{e2}'
        img_placements_comparison_row[col] = 0 
        if img_placements[e1] != img_placements[e2]:
            img_placements_comparison_row[col] = 1
            s1, s2 = set(img_placements[e1]), set(img_placements[e2])
            LOGGER.debug(f'img_placements not equal:\n\t{(s1 - s2) | (s2 - s1)}')
        num_imgs_comparison_row[col] = 0 
        if num_imgs[e1] != num_imgs[e2]:
            num_imgs_comparison_row[col] = 1 
            LOGGER.debug(f'num_imgs not equal: \n\t{num_imgs[e1]}\n\t{num_imgs[e2]}')
        img_info_comparison_row[col] = 0 if compare_all_img_infos(img_infos[e1], img_infos[e2]) else 1
    rows = [num_imgs_comparison_row, img_placements_comparison_row, img_info_comparison_row]
    df = pd.concat([df, pd.DataFrame.from_records(rows, index=DF_COMPARISON_INDEX)])
    return df

def compute_edit_ops_metrics(edit_ops_results, results_df):
    row : Dict[str, Any] = { 'comparison': 'insert_minus_delete' }
    for cmp_engines, df in edit_ops_results.items():
        grouped = df.groupby('action', as_index=True)['count'].sum()
        insertions = 0 if 'insert' not in grouped.index else grouped.at['insert']
        deletions = 0 if 'delete' not in grouped.index else grouped.at['delete']
        row[cmp_engines] = insertions - deletions
    results_df = pd.concat([results_df, pd.DataFrame.from_records([row], index=DF_COMPARISON_INDEX)])
    return results_df

def get_text_and_images_from_pdf(arxiv_id, transformer):
    pdf_pages, pdf_images = extract_pages_and_images_from_pdfs(COMPILED_FOLDER, arxiv_id)
    pdf_texts = process_pages_to_string(pdf_pages, transformer)
    return pdf_texts, pdf_images

# </ runners > -----------------------------------------------------------------

COMPARE_METHODS = {
    'levenshtein': Levenshtein.distance,
    'hamming': Levenshtein.hamming,
    'levenshtein_ratio': Levenshtein.ratio,
    'levenshtein_normalised': normalise(Levenshtein.distance),
    'hamming_normalised': normalise(Levenshtein.hamming),
}

DEFAULT_TRANSFORMER = Ttr.transformer_ignore_hyphenbreak_pagebreak_linebreak

def extract_pdf_text_to_save_file(arxiv_id, transformer=DEFAULT_TRANSFORMER):
    pdf_texts, pdf_images = get_text_and_images_from_pdf(arxiv_id, transformer)
    # save to file
    for engine, text in pdf_texts.items():
        helpers.save_to_file(text, f'{arxiv_id}_{engine}_pdftext.txt')
    for engine, image_info_nested_list in pdf_images.items():
        img_info_flatlist = [item for row in image_info_nested_list for item in row]
        img_infos_as_text = '\n'.join([ f"{img_info['digest']}  {img_info}" for img_info in img_info_flatlist ])
        helpers.save_to_file(img_infos_as_text, f'{arxiv_id}_{engine}_pdfimages.txt')
    return

def main(arxiv_id):
    LOGGER.debug(pad_with_char(f'[{arxiv_id}]: running comparison', '='))
    pdf_texts, pdf_images = get_text_and_images_from_pdf(arxiv_id, transformer=DEFAULT_TRANSFORMER)

    edit_ops_results = compute_edit_ops(pdf_texts)
    analysed_edit_opts_results = analyse_edit_opts_results(edit_ops_results)
    cleaned_results, summary = compute_cleaned_edit_ops(edit_ops_results)

    RESULTS = helpers.init_df_with_cols([DF_COMPARISON_INDEX] + [f'{e1}{e2}' for e1, e2 in COMPARISON], DF_COMPARISON_INDEX)
    RESULTS = compute_text_comparison_metrics(COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compute_levenshtein_cleaned_and_edit_ops_summary(cleaned_results, summary, RESULTS)
    RESULTS = compute_image_comparison_metrics(pdf_images, RESULTS)
    RESULTS = compute_edit_ops_metrics(edit_ops_results, RESULTS)

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

    LOGGER.debug('comparison summary:\n' + RESULTS.to_string())
    LOGGER.debug(pad_with_char(f' completed {arxiv_id}', '='))
    return RESULTS


