import os
import pandas as pd
import subprocess
from typing import Dict, Any
from datetime import datetime
from tqdm import tqdm
from analysis.helpers import init_df_with_cols
from config import COMPILED_FOLDER, LOGS_FOLDER
from utils.tex_engine_utils import TEX_ENGINES as ENGINES, DIFF_ENGINE_PAIRS as COMPARISON, get_engine_name

def init_df():
    # set up dataframe
    results_column_names = ['arxiv_id'] + [ f'{get_engine_name(e)}_pages' for e in ENGINES ] + [ f'diff_{e1}{e2}' for e1, e2 in COMPARISON ]
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
            pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{get_engine_name(engine)}.pdf')
            num_pages = count_pdf_pages(pdf_path)
            if num_pages is not None: row[f'{get_engine_name(engine)}_pages'] = num_pages
        for e1, e2 in COMPARISON:
            col1, col2 = f'{get_engine_name(e1)}_pages', f'{get_engine_name(e2)}_pages'
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
