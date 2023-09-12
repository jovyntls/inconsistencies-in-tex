from utils import tex_engine_utils
from utils.logger import LOGGER
from config import LOGS_FOLDER, PIXEL_TOLERANCE
import os
import subprocess

def compare_engine_outputs(arxiv_id, COMPILED_FOLDER, DIFFS_FOLDER, RESULTS):
    def get_diff_command(e1, e2, pixel_tolerance=2000):
        def output_filename(engine, arxiv_id):
            return os.path.join(os.path.join(COMPILED_FOLDER, arxiv_id), f'{arxiv_id}_{engine}.pdf')
        diff_output = os.path.join(DIFFS_FOLDER, f'diff_{arxiv_id}_{e1}_{e2}.pdf')
        return ['diff-pdf', f'--output-diff={diff_output}', '-smg', '--dpi=100', f'--per-page-pixel-tolerance={pixel_tolerance}', output_filename(e1, arxiv_id), output_filename(e2, arxiv_id)] 

    # returns bool of whether they match
    def diff_engines(e1, e2):
        try:
            subprocess.run(get_diff_command(e1, e2, PIXEL_TOLERANCE), check=True)
            LOGGER.debug(f"[{arxiv_id}] no diffs for [{e1}] <> [{e2}]")
            return True
        except subprocess.CalledProcessError as e:
            LOGGER.debug(f"diff-pdf: [{arxiv_id}] ret={e.returncode} for [{e1}] <> [{e2}]")
            return False

    for engine1, engine2 in tex_engine_utils.DIFF_ENGINE_PAIRS:
        try:
            engine1_ret, engine2_ret = RESULTS.at[arxiv_id, engine1], RESULTS.at[arxiv_id, engine2]
            if engine1_ret != 0 or engine2_ret != 0:
                LOGGER.debug(f'compare_engine_outputs: [{arxiv_id}] {engine1}<>{engine2} had compile failures, but attempting to diff anyway')
            # diff the PDFs
            pdfs_equal = diff_engines(engine1, engine2)
            RESULTS.at[arxiv_id, f'{engine1[:-5]}<>{engine2[:-5]}'] = pdfs_equal
        except KeyError:
            LOGGER.debug(f'compare_engine_outputs: [{arxiv_id}] no compile result found for {engine1}<>{engine2}')
    return RESULTS

def main(COMPILED_FOLDER, DIFFS_FOLDER, RESULTS):
    LOGGER.info(f'diffing output pdfs...')
    for arxiv_id in os.listdir(COMPILED_FOLDER):
        # compare the output pdfs
        RESULTS = compare_engine_outputs(arxiv_id, COMPILED_FOLDER, DIFFS_FOLDER, RESULTS)
    LOGGER.debug('intermediate results:\n' + RESULTS.to_string())
    RESULTS.to_csv(os.path.join(LOGS_FOLDER, f'{current_time}_intermediate_results.csv'))
    return RESULTS
