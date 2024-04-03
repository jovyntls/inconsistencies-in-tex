"""
use the -e '$bibtex_fudge=1;' option, and only for 2020
"""
import os
import time
import argparse
import subprocess
import csv
from tqdm import tqdm
from pipeline.compile_tex_files import find_entrypoint_file

# these depend on the dockerfile
DOCKER_PROJECT_ROOT = '/diff_test_tex_engines'
EXTRACTED_FOLDER = os.path.join(DOCKER_PROJECT_ROOT, 'bin', 'tex_sources')
DOCKER_BIN = os.path.join(DOCKER_PROJECT_ROOT, 'docker_bin_2')

LATEXMK_COMPILE_CMD_BASE  = [ 'latexmk', '-pdf', '-interaction=nonstopmode' ]
LATEXMK_COMPILE_FLAG = [ '-e', '$bibtex_fudge=1;' ] 

def checkpaths(texlive_version, VERSION_COMPILED_FOLDER, COMPILE_RESULTS_FOLDER):
    if not os.path.isdir(EXTRACTED_FOLDER): 
        raise Exception(f'could not find {EXTRACTED_FOLDER=}')
    print(f'found {len(os.listdir(EXTRACTED_FOLDER))} items in {EXTRACTED_FOLDER=}')

    if os.path.isdir(VERSION_COMPILED_FOLDER):
        print(f'found {VERSION_COMPILED_FOLDER=} with {len(os.listdir(VERSION_COMPILED_FOLDER))} items')
    else:
        print(f'creating {VERSION_COMPILED_FOLDER=}')
        os.makedirs(VERSION_COMPILED_FOLDER)

    results_file = os.path.join(COMPILE_RESULTS_FOLDER, f'results_{texlive_version}.csv')
    if os.path.isfile(results_file):
        raise Exception(f'results file already exists: {results_file}')
    os.makedirs(COMPILE_RESULTS_FOLDER, exist_ok=True)

def compile_tex_to_pdf(texlive_version, with_flag, root, tex_file, logs_folder, arxiv_id, output_folder):
    compile_command = LATEXMK_COMPILE_CMD_BASE + LATEXMK_COMPILE_FLAG if with_flag else LATEXMK_COMPILE_CMD_BASE
    compile_command += [ f'-jobname={arxiv_id}_tl{texlive_version}', f'-output-directory={output_folder}', tex_file ]
    latexmk_run_1, latexmk_run_2  = -1, -1
    try:
        stdout_file = os.path.join(logs_folder, f'{arxiv_id}_tl{texlive_version}.out')
        stderr_file = os.path.join(logs_folder, f'{arxiv_id}_tl{texlive_version}.err')
        with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
            time_1 = time.time()
            proc = subprocess.run(compile_command, timeout=300, stdout=stdout, stderr=stderr, cwd=root)
            time_2 = time.time()
            proc = subprocess.run(compile_command, timeout=300, stdout=stdout, stderr=stderr, cwd=root)
            time_3 = time.time()
            latexmk_run_1, latexmk_run_2 = time_2 - time_1, time_3 - time_2
            return proc.returncode, latexmk_run_1, latexmk_run_2
    except subprocess.TimeoutExpired:
        return 'TIMED_OUT', latexmk_run_1, latexmk_run_2

def run(texlive_version, with_flag, VERSION_COMPILED_FOLDER, COMPILE_RESULTS_FOLDER):
    results = {}
    a_results_csv_filepath = os.path.join(COMPILE_RESULTS_FOLDER, f'a_results_{tl_version}.csv')
    with open(a_results_csv_filepath,'a') as f:
        a_writer = csv.writer(f)
        for arxiv_id in tqdm(os.listdir(EXTRACTED_FOLDER)):
            # create the subdirs for output, if it doesn't exist
            compile_output_folder = os.path.join(VERSION_COMPILED_FOLDER, arxiv_id)
            compile_logs_folder = os.path.join(compile_output_folder, 'logs')
            os.makedirs(compile_output_folder, exist_ok=True)
            os.makedirs(compile_logs_folder, exist_ok=True)
            # run compilation
            for root, _, files in os.walk(os.path.join(EXTRACTED_FOLDER, arxiv_id)):
                tex_file, docclass, _ = find_entrypoint_file(files, root)
                if tex_file is None: continue
                # if entrypoint is identified, begin compilation
                ret = compile_tex_to_pdf(texlive_version, with_flag, root, tex_file, compile_logs_folder, arxiv_id, compile_output_folder)
                results[arxiv_id] = (ret[0], docclass, ret[1], ret[2])
                break
            else:
                results[arxiv_id] = (-1, 'NO_ENTRYPOINT', -1, -1)
            a_writer.writerow([arxiv_id] + list(results[arxiv_id]))
            f.flush()  # save immediately
    return results

def save_results(results, texlive_version, COMPILE_RESULTS_FOLDER):
    results_csv_filepath = os.path.join(COMPILE_RESULTS_FOLDER, f'results_{texlive_version}.csv')
    with open(results_csv_filepath, 'w') as csv_file:  
        writer = csv.writer(csv_file)
        for arxiv_id, res in results.items():
            ret, docclass, time_1, time_2 = res
            writer.writerow([arxiv_id, ret, docclass, time_1, time_2])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run text-based comparison (text, formatting, images)')
    parser.add_argument('-ver', required=True, help="texlive version for labelling")
    parser.add_argument('-flags', action='store_true', help="add the $bibtex_fudge=1; flag to compilation (for tl2020)")
    tl_version, with_flag = parser.parse_args().ver, parser.parse_args().flags

    VERSION_COMPILED_FOLDER = os.path.join(DOCKER_BIN, 'version_compiled_pdf_2020' if with_flag else 'version_compiled_pdf')
    COMPILE_RESULTS_FOLDER = os.path.join(DOCKER_BIN, 'compile_results_2020' if with_flag else 'compile_results')

    checkpaths(tl_version, VERSION_COMPILED_FOLDER, COMPILE_RESULTS_FOLDER)
    results = run(tl_version, with_flag, VERSION_COMPILED_FOLDER, COMPILE_RESULTS_FOLDER)
    save_results(results, tl_version, COMPILE_RESULTS_FOLDER)



