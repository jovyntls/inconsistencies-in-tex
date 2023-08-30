from utils.logger import Log_level
from utils import tex_engine_utils

import os
import subprocess
import re
import pandas as pd

def find_entrypoint_file(files):
    # 0. check if it is a single uncompressed tex file
    for file in files:
        # ideally check len(files)==1, but not always true since aux files will be there if code is rerun
        if re.search(r'\d{4}\.\d+', file) is not None:
            return file
    # 1. match any entrypoint
    ENTRYPOINTS = { 'main.tex', 'manuscript.tex', 'mainnew.tex' }
    # 2. try these
    ENTRYPOINT_REGEXES =[ r'main.*\.tex$', r'.+\.tex$' ]

    exact_matches = ENTRYPOINTS.intersection(files)
    if len(exact_matches) > 0:
        return list(exact_matches)[0]
    for pattern in ENTRYPOINT_REGEXES:
        for file in files:
            match = re.search(pattern, file, re.IGNORECASE)
            if match: return file
    return None

def create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id):
    output_folder = os.path.join(COMPILED_FOLDER, arxiv_id)
    logs_folder = os.path.join(output_folder, 'logs')
    os.makedirs(output_folder, exist_ok=False)
    os.makedirs(logs_folder, exist_ok=False)
    return output_folder, logs_folder

def run_tex_engines(project_root, tex_file, logs_folder, arxiv_id, output_folder, LOGGER):
    # run all tex engines
    COMPILE_TEX_COMMANDS = tex_engine_utils.get_compile_tex_commands(arxiv_id, output_folder)
    rets = {}
    for tex_engine, run_command in COMPILE_TEX_COMMANDS.items():
        try:
            stdout_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.out')
            stderr_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.err')
            with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
                cmd = run_command + [tex_file]
                # first compile
                proc = subprocess.run(cmd, timeout=60, stdout=stdout, stderr=stderr, cwd=project_root)
                LOGGER.log(Log_level.DEBUG, f'compile_tex (1): ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
                if proc.returncode == 0:
                    # second compile
                    proc = subprocess.run(cmd, timeout=60, stdout=stdout, stderr=stderr, cwd=project_root)
                    LOGGER.log(Log_level.DEBUG, f'compile_tex (2): ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
                rets[tex_engine] = proc.returncode
                # log if the compile failed
                if proc.returncode != 0: LOGGER.log(Log_level.WARN, f'compile_tex: ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
        except subprocess.TimeoutExpired:
            LOGGER.log(Log_level.ERROR, f"compile_tex: timed out for {arxiv_id} [{tex_engine}]")
    return rets

def should_skip_compile(tex_file):
    with open(tex_file) as f:
        return '{IEEEtran}' in f.read()

def main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS, LOGGER):
    LOGGER.log(Log_level.INFO, f'compiling tex files...')
    skipped_files = []
    results_to_concat = []
    for arxiv_id in os.listdir(EXTRACTED_FOLDER):
        folder_path = os.path.join(EXTRACTED_FOLDER, arxiv_id)
        output_folder, logs_folder = create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id)
        # try to find a tex file
        for root, _, files in os.walk(folder_path):
            tex_file = find_entrypoint_file(files)
            if tex_file is None: 
                LOGGER.log(Log_level.WARN, f'could not find entrypoint tex file: [{arxiv_id}]')
                continue
            LOGGER.log(Log_level.DEBUG, f'found latex file: [{arxiv_id}] {tex_file}')
            # skip compiles for IEEEtran files as they have known diffs
            if should_skip_compile(os.path.join(root, tex_file)): 
                skipped_files.append(f'{arxiv_id}/{tex_file}')
                LOGGER.log(Log_level.DEBUG, f'skipping file: [{arxiv_id}] uses IEEE {tex_file}')
                break
            # run the tex engines
            rets = run_tex_engines(root, tex_file, logs_folder, arxiv_id, output_folder, LOGGER)
            # convert to a new df row
            rets['arxiv_id'] = arxiv_id
            rets['entrypoint'] = tex_file
            results_to_concat.append(rets)
            break
    RESULTS = pd.concat([RESULTS, pd.DataFrame.from_records(results_to_concat, index='arxiv_id')])
    LOGGER.log(Log_level.INFO, f'compiled: {len(RESULTS.index)} papers.\tskipped: {len(skipped_files)} papers.')
    LOGGER.log(Log_level.DEBUG, f'skipped {len(skipped_files)} papers: {skipped_files}')
    LOGGER.log(Log_level.DEBUG, RESULTS)
    return RESULTS
