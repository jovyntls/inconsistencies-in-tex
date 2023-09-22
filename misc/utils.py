import pandas as pd
import os
from config import PROJECT_ROOT

ENGINES = ['pdf', 'xe', 'lua']
COMPARISON = [ ('xe', 'pdf'), ('xe', 'lua') ]

def init_df_with_cols(cols, index):
    df = pd.DataFrame(columns=cols)
    if index != None: df = df.set_index(index)
    return df

def save_to_file(string, filename):
    MISC_BIN_FOLDER = os.path.join(PROJECT_ROOT, 'misc/bin')
    os.makedirs(MISC_BIN_FOLDER, exist_ok=True)
    file_path = os.path.join(MISC_BIN_FOLDER, filename)
    with open(file_path, 'w') as file:
        file.write(string)
    print(f"saved to file [{filename}] in misc/bin/")


