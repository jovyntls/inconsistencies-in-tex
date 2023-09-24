import os
import fitz  # imports the pymupdf library
import Levenshtein
import pandas as pd
import analysis.helpers as helpers
from analysis.helpers import ENGINES, COMPARISON
import analysis.text_transformer as Ttr
from config import COMPILED_FOLDER, YEAR_AND_MONTH

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
        pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{engine}latex.pdf')
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
        'aspect_ratio': width/height,
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
        normalised_score = 1 - (score / max_length)
        return normalised_score
    return compare

def cmp_with_threshold(v1, v2, threshold=0.01):
    val1, val2 = min(v1, v2), max(v1, v2)
    diff = val2 - val1
    return diff/val1 < threshold

def cmp_img_info(info1, info2):
    pos_identical = cmp_with_threshold(info1['pos'][0], info2['pos'][0]) and cmp_with_threshold(info1['pos'][1], info2['pos'][1])
    if not pos_identical: return False
    ar_identical = cmp_with_threshold(info1['aspect_ratio'], info2['aspect_ratio'])
    if not ar_identical: return False
    width_identical = cmp_with_threshold(info1['width'], info2['width'])
    if not width_identical: return False
    height_identical = cmp_with_threshold(info1['height'], info2['height'])
    if not height_identical: return False
    return True

def compare_all_img_infos(l1, l2):
    if len(l1) != len(l2): return False
    for img_id in l1.keys():
        if img_id not in l2: return False
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
        case _:
            print(f'unknown op: {action}')

def get_edit_ops(text1, text2):
    ops = Levenshtein.editops(text1, text2)
    return [transform_op(op, text1, text2) for op in ops]

def collate_edit_ops(edit_ops):
    collated = {}
    for action, _, _, src_char, dest_char in edit_ops:
        op_index = (action, src_char, dest_char)
        if op_index not in collated: collated[op_index] = 0
        collated[op_index] += 1
    return collated

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
    def compute_edit_ops_for_engine(e1, e2):
        edit_ops = get_edit_ops(pdf_texts[e1], pdf_texts[e2])
        collated_ops = collate_edit_ops(edit_ops)
        data = [ ( *op, counts ) for op, counts in collated_ops.items() ]
        df = pd.DataFrame(data, columns =[ 'action', 'from', 'to', 'count' ])
        return df.sort_values(by=['count'], ascending=False)
    RESULTS = {}
    for e1, e2 in COMPARISON:
        if e1 not in pdf_texts or e2 not in pdf_texts: continue
        RESULTS[f'{e1}{e2}'] = compute_edit_ops_for_engine(e1, e2)
    return RESULTS

def compute_cleaned_edit_ops(edit_ops_results):
    cleaned_results = {}
    summary = {}
    for e1, e2 in COMPARISON:
        cmp = f'{e1}{e2}'
        if cmp not in edit_ops_results: continue
        cleaned_results[cmp], summary[cmp] = clean_edit_ops_results(edit_ops_results[cmp])
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
    img_placements_comparison_row = { 'comparison': 'img_placements' }
    num_imgs_comparison_row = { 'comparison': 'num_images' }
    img_info_comparison_row = { 'comparison': 'img_info' }
    for e1, e2 in COMPARISON:
        if e1 not in pdf_images or e2 not in pdf_images: continue
        col = f'{e1}{e2}'
        img_placements_comparison_row[col] = 0 if img_placements[e1] == img_placements[e2] else 1
        num_imgs_comparison_row[col] = 0 if num_imgs[e1] == num_imgs[e2] else 1
        img_info_comparison_row[col] = 0 if compare_all_img_infos(img_infos[e1], img_infos[e2]) else 1
    rows = [num_imgs_comparison_row, img_placements_comparison_row, img_info_comparison_row]
    df = pd.concat([df, pd.DataFrame.from_records(rows, index=DF_COMPARISON_INDEX)])
    return df

def compute_edit_ops_metrics(edit_ops_results, results_df):
    row = { 'comparison': 'insert_minus_delete' }
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
    'ratio': Levenshtein.ratio,
    'levenshtein_normalised': normalise(Levenshtein.distance),
    'hamming_normalised': normalise(Levenshtein.hamming),
}

DEFAULT_TRANSFORMER = Ttr.transformer_ignore_hyphenbreak_pagebreak_linebreak

def extract_pdf_text_to_save_file(arxiv_id, transformer=DEFAULT_TRANSFORMER):
    pdf_texts, _ = get_text_and_images_from_pdf(f'{YEAR_AND_MONTH}.{arxiv_id}', transformer)
    # save to file
    for engine, text in pdf_texts.items():

        helpers.save_to_file(text, f'{arxiv_id}_{engine}_pdftext.txt')
    return

def main(user_input):
    # user_input = input('arxiv_id: ').strip()
    # if len(user_input) != 5: return print('invalid input')
    arxiv_id = f'{YEAR_AND_MONTH}.{user_input}'

    pdf_texts, pdf_images = get_text_and_images_from_pdf(arxiv_id, transformer=DEFAULT_TRANSFORMER)

    edit_ops_results = compute_edit_ops(pdf_texts)
    analysed_edit_opts_results = analyse_edit_opts_results(edit_ops_results)
    cleaned_results, summary = compute_cleaned_edit_ops(edit_ops_results)

    RESULTS = helpers.init_df_with_cols([DF_COMPARISON_INDEX, 'xepdf', 'xelua'], DF_COMPARISON_INDEX)
    RESULTS = compute_text_comparison_metrics(COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compute_image_comparison_metrics(pdf_images, RESULTS)
    RESULTS = compute_edit_ops_metrics(edit_ops_results, RESULTS)

    for e1, e2 in COMPARISON:
        cmp = f'{e1}{e2}'
        print(f'\n————— {cmp}', '—'*30)
        if not cmp in edit_ops_results:
            if e1 not in pdf_texts: print(e1, 'not found')
            if e2 not in pdf_texts: print(e2, 'not found')
            continue
        if edit_ops_results[cmp].shape[0] == 0: 
            print('\nno text diffs found')
            continue
        print(f'\n>> edit ops [{cmp}] [{edit_ops_results[cmp].shape[0]} rows]:')
        print(analysed_edit_opts_results[cmp])
        print('___')
        print(edit_ops_results[cmp].head(15))
        print(f'\n>> cleaned edit ops [{cmp}] [{cleaned_results[cmp].shape[0]} rows]:')
        print(cleaned_results[cmp])
        print(summary[cmp])
    print('\n' + '—'*42 + '\n')

    print(RESULTS)


