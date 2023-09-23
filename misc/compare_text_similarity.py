import os
import fitz  # imports the pymupdf library
import Levenshtein
import pandas as pd
import misc.utils as utils
import misc.text_transformer as Ttr
from config import COMPILED_FOLDER, YEAR_AND_MONTH

DF_COMPARISON_INDEX = 'comparison'

# < PDF to string helpers > ---------------------------------------------------

def extract_pages_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text() for page in doc]
        images = [page.get_images() for page in doc]
        return pages, images
    except:
        return None, None

def extract_pages_and_images_from_pdfs(COMPILED_FOLDER, arxiv_id):
    compiled_pdfs_dir = os.path.join(COMPILED_FOLDER, arxiv_id)
    pdf_texts = {}
    pdf_images = {}
    for engine in utils.ENGINES:
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

# </ PDF to string helpers > --------------------------------------------------

# < text comparison helpers > -------------------------------------------------

def compare_texts_with_method(pdf_texts, compare_f):
    result = {}
    for e1, e2 in utils.COMPARISON:
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
    for e1, e2 in utils.COMPARISON:
        RESULTS[f'{e1}{e2}'] = compute_edit_ops_for_engine(e1, e2)
    return RESULTS

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
    # pdf_images: { engine -> [[imgs], [imgs]] }
    # img_counts: { engine -> [count, count] }
    # imgs_with_pagenum: { engine -> [(img, pg), (img, pg), (img, pg)] }
    # compute the counts
    num_imgs = { engine: sum([len(imgs_in_pg) for imgs_in_pg in imgs]) for engine, imgs in pdf_images.items() }
    img_placements = { engine: [] for engine in pdf_images.keys() }
    for engine, imgs_by_page in pdf_images.items():
        for page_index, imgs_in_page in enumerate(imgs_by_page):
            img_placements[engine] += [ (page_index + 1, img) for img in imgs_in_page ]
    # compute the comparisons
    img_placements_comparison_row = { 'comparison': 'img_placements' }
    num_imgs_comparison_row = { 'comparison': 'num_images' }
    for e1, e2 in utils.COMPARISON:
        col = f'{e1}{e2}'
        img_placements_comparison_row[col] = 0 if img_placements[e1] == img_placements[e2] else 1
        num_imgs_comparison_row[col] = 0 if num_imgs[e1] == num_imgs[e2] else 1
    rows = [num_imgs_comparison_row, img_placements_comparison_row]
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

        utils.save_to_file(text, f'{arxiv_id}_{engine}_pdftext.txt')
    return

def main(user_input):
    # user_input = input('arxiv_id: ').strip()
    # if len(user_input) != 5: return print('invalid input')
    arxiv_id = f'{YEAR_AND_MONTH}.{user_input}'

    # TODO: size of images
    pdf_texts, pdf_images = get_text_and_images_from_pdf(arxiv_id, transformer=DEFAULT_TRANSFORMER)

    edit_ops_results = compute_edit_ops(pdf_texts)
    analysed_edit_opts_results = analyse_edit_opts_results(edit_ops_results)

    RESULTS = utils.init_df_with_cols([DF_COMPARISON_INDEX, 'xepdf', 'xelua'], DF_COMPARISON_INDEX)
    RESULTS = compute_text_comparison_metrics(COMPARE_METHODS, pdf_texts, RESULTS)
    RESULTS = compute_image_comparison_metrics(pdf_images, RESULTS)
    RESULTS = compute_edit_ops_metrics(edit_ops_results, RESULTS)

    for cmp_engines, res in edit_ops_results.items():
        print(f'\n{cmp_engines} [{res.shape[0]} rows]')
        print(res.head(15))
        print('\n', analysed_edit_opts_results[cmp_engines])
    print(RESULTS)


