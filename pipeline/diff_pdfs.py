from utils.tex_engine_utils import get_engine_name, DIFF_ENGINE_PAIRS
from utils.logger import PIPELINE_LOGGER as LOGGER
from config import PIXEL_TOLERANCE, USE_TL2020_DIR
import os
import subprocess
from tqdm import tqdm

def compare_engine_outputs(arxiv_id, COMPILED_FOLDER, COMPILED_FOLDER_2020, DIFFS_FOLDER, RESULTS):
    def get_diff_command(e1, e2):
        def output_filename(engine, arxiv_id):
            if USE_TL2020_DIR and engine == '20': 
                return os.path.join(os.path.join(COMPILED_FOLDER_2020, arxiv_id), f'{arxiv_id}_{get_engine_name(engine)}.pdf')
            return os.path.join(os.path.join(COMPILED_FOLDER, arxiv_id), f'{arxiv_id}_{get_engine_name(engine)}.pdf')
        diff_output = os.path.join(DIFFS_FOLDER, f'diff_{arxiv_id}_{e1}_{e2}.pdf')
        return ['diff-pdf', f'--output-diff={diff_output}', '-smg', '--dpi=300', f'--per-page-pixel-tolerance={PIXEL_TOLERANCE}', output_filename(e1, arxiv_id), output_filename(e2, arxiv_id)] 

    # returns bool of whether they match
    def diff_engines(e1, e2):
        try:
            subprocess.run(get_diff_command(e1, e2), check=True)
            LOGGER.debug(f"[{arxiv_id}] no diffs for [{e1}] <> [{e2}]")
            return True
        except subprocess.CalledProcessError as e:
            LOGGER.debug(f"diff-pdf: [{arxiv_id}] ret={e.returncode} for [{e1}] <> [{e2}]")
            return False

    for engine1, engine2 in DIFF_ENGINE_PAIRS:
        try:
            # engine1_ret, engine2_ret = RESULTS.at[arxiv_id, engine1], RESULTS.at[arxiv_id, engine2]
            # if engine1_ret != 0 or engine2_ret != 0:
            #     LOGGER.debug(f'compare_engine_outputs: [{arxiv_id}] {engine1}<>{engine2} had compile failures, but attempting to diff anyway')
            # diff the PDFs
            pdfs_equal = diff_engines(engine1, engine2)
            RESULTS.at[arxiv_id, f'{engine1}<>{engine2}'] = pdfs_equal
        except KeyError:
            LOGGER.debug(f'compare_engine_outputs: [{arxiv_id}] no compile result found for {engine1}<>{engine2}')
    return RESULTS

def main(COMPILED_FOLDER, COMPILED_FOLDER_2020, DIFFS_FOLDER, RESULTS):
    LOGGER.info(f'diffing output pdfs...')
    for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER)):
        # compare the output pdfs
        RESULTS = compare_engine_outputs(arxiv_id, COMPILED_FOLDER, COMPILED_FOLDER_2020, DIFFS_FOLDER, RESULTS)
    return RESULTS
