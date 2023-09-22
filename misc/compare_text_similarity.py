import os
import fitz  # imports the pymupdf library
import Levenshtein
import pandas as pd
import misc.utils as utils
from config import COMPILED_FOLDER

DF_COMPARISON_INDEX = 'comparison'

def init_df():
    cols = [DF_COMPARISON_INDEX, 'xepdf', 'xelua']
    return utils.init_df_with_cols(cols, DF_COMPARISON_INDEX)

def extract_pages_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text() for page in doc]
        return pages
    except:
        return None

def extract_pages_from_pdfs(COMPILED_FOLDER, arxiv_id):
    compiled_pdfs_dir = os.path.join(COMPILED_FOLDER, arxiv_id)
    # get text from PDF
    pdf_texts = {}
    for engine in utils.ENGINES:
        pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{engine}latex.pdf')
        pages = extract_pages_from_pdf(pdf_path)
        if pages != None: 
            pdf_texts[engine] = pages
    return pdf_texts

def process_pages_to_string(engine_to_pages, process_f):
    pdf_texts = {}
    for engine, pages in engine_to_pages.items():
        if pages == None: continue
        pdf_texts[engine] = process_f(pages)
    return pdf_texts

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

def process_ignore_pagebreak_linebreak(pages_arr):
    # replace linebreaks with space
    pages_arr = [page.replace('\n', ' ') for page in pages_arr]
    # replace pagebreaks with space
    return ' '.join(pages_arr)

def process_ignore_hyphenbreak_pagebreak_linebreak(pages_arr):
    # replace linebreaks with space
    pages_arr = [page.replace('-\n','\n').replace('\n', ' ') for page in pages_arr]
    # replace pagebreaks with space
    return ' '.join(pages_arr)

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

def compute_comparison_metrics(COMPARE_METHODS, pdf_texts):
    RESULTS = []
    for method_name, f in COMPARE_METHODS.items():
        row = compare_texts_with_method(pdf_texts, f)
        row[DF_COMPARISON_INDEX] = method_name
        RESULTS.append(row)
    # save compare text results to a df
    df = init_df()
    df = pd.concat([df, pd.DataFrame.from_records(RESULTS, index=DF_COMPARISON_INDEX)])
    return df

def get_text_from_pdf(arxiv_id, process_f):
    pdf_pages = extract_pages_from_pdfs(COMPILED_FOLDER, arxiv_id)
    pdf_texts = process_pages_to_string(pdf_pages, process_f)
    return pdf_texts

COMPARE_METHODS = {
    'levenshtein': Levenshtein.distance,
    'hamming': Levenshtein.hamming,
    'ratio': Levenshtein.ratio,
    'levenshtein_normalised': normalise(Levenshtein.distance),
    'hamming_normalised': normalise(Levenshtein.hamming),
}

def extract_pdf_text_to_save_file(arxiv_id, process_f=process_ignore_hyphenbreak_pagebreak_linebreak):
    pdf_texts = get_text_from_pdf('2306.' + arxiv_id, process_f)
    # save to file
    for engine, text in pdf_texts.items():
        utils.save_to_file(text, f'{arxiv_id}_{engine}_pdftext.txt')
    return

def main(user_input):
    # user_input = input('arxiv_id: ').strip()
    # if len(user_input) != 5: return print('invalid input')
    arxiv_id = '2306.' + user_input

    pdf_texts = get_text_from_pdf(arxiv_id, process_f=process_ignore_hyphenbreak_pagebreak_linebreak)
    comparison_results = compute_comparison_metrics(COMPARE_METHODS, pdf_texts)
    edit_ops_results = compute_edit_ops(pdf_texts)

    for cmp_engines, res in edit_ops_results.items():
        print(f'\n{cmp_engines} [{res.shape[0]} rows]')
        print(res.head(10))
    print(comparison_results)

