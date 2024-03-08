import os
import pandas as pd
import subprocess
from typing import Dict, Any
from datetime import datetime
from tqdm import tqdm
from analysis.helpers import init_df_with_cols
from config import EXTRACTED_FOLDER, COMPILED_FOLDER, LOGS_FOLDER
from utils.tex_engine_utils import TEX_ENGINES as ENGINES, get_engine_name

def init_df():
    # set up dataframe
    results_column_names = [ 'arxiv_id' ] + ENGINES
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
    arxiv_ids_extracted = os.listdir(EXTRACTED_FOLDER)
    results = []
    for arxiv_id in tqdm(arxiv_ids_extracted):
        compiled_pdfs_dir = os.path.join(COMPILED_FOLDER, arxiv_id)
        row : Dict[str, Any] = { 'arxiv_id': arxiv_id }
        for engine in ENGINES:
            pdf_path = os.path.join(compiled_pdfs_dir, f'{arxiv_id}_{get_engine_name(engine)}.pdf')
            row[engine] = os.path.exists(pdf_path)
        results.append(row)
    df = init_df()
    df = pd.concat([df, pd.DataFrame.from_records(results, index='arxiv_id')])
    print(df)
    print(df.to_csv())
    # save results to a csv
    if should_save:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(LOGS_FOLDER, f'num_compiled_pdfs_{current_time}.csv')
        df.to_csv(save_path)
        print(f'saved to {save_path}')
