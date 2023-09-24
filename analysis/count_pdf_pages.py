import os
import pandas as pd
import subprocess
from typing import Dict, Any
from datetime import datetime
from tqdm import tqdm
from analysis.helpers import ENGINES, COMPARISON, init_df_with_cols
from config import COMPILED_FOLDER, LOGS_FOLDER

ENGINES = ['pdf', 'xe', 'lua']
COMPARISON = [ ('xe', 'pdf'), ('xe', 'lua') ]

def init_df():
    # set up dataframe
    results_column_names = [ 'arxiv_id', 'pdflatex_pages', 'xelatex_pages', 'lualatex_pages', 'diff_xepdf', 'diff_xelua' ]
    return init_df_with_cols(results_column_names, 'arxiv_id')

def count_pdf_pages(pdf_path):
    try:
        out = subprocess.getoutput(f'pdfinfo {pdf_path} | grep Pages:')
        out = out.strip().replace(' ', '')
        if out[:6] == 'Pages:': return int(out[6:])
        return None
    except:
        return None

def main(should_save=True):
    dirs = os.listdir(COMPILED_FOLDER)
    results = []
    for arxiv_id in tqdm(dirs):
        compiled_pdfs_dir = os.path.join(COMPILED_FOLDER, arxiv_id)
        row : Dict[str, Any] = { 'arxiv_id': arxiv_id }
        for engine in ENGINES:
            pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{engine}latex.pdf')
            num_pages = count_pdf_pages(pdf_path)
            if num_pages is not None: row[f'{engine}latex_pages'] = num_pages
        for e1, e2 in COMPARISON:
            col1, col2 = f'{e1}latex_pages', f'{e2}latex_pages'
            if col1 in row and col2 in row:
                row[f'diff_{e1}{e2}'] = 0 if row[col1] == row[col2] else 1
        results.append(row)
    df = init_df()
    df = pd.concat([df, pd.DataFrame.from_records(results, index='arxiv_id')])
    print(df)
    print(df.to_csv())
    # save results to a csv
    if should_save:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        df.to_csv(os.path.join(LOGS_FOLDER, f'num_pages_{current_time}.csv'))
