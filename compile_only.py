import os
import argparse
import subprocess
import csv
from tqdm import tqdm
from pipeline.compile_tex_files import find_entrypoint_file

# these depend on the dockerfile
DOCKER_PROJECT_ROOT = '/diff_test_tex_engines'
EXTRACTED_FOLDER = os.path.join(DOCKER_PROJECT_ROOT, 'bin', 'tex_sources')
VERSION_COMPILED_FOLDER = os.path.join(DOCKER_PROJECT_ROOT, 'docker_bin', 'version_compiled_pdf')
COMPILE_RESULTS_FOLDER = os.path.join(DOCKER_PROJECT_ROOT, 'docker_bin', 'compile_results')

def checkpaths(texlive_version):
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

def compile_tex_to_pdf(texlive_version, root, tex_file, logs_folder, arxiv_id, output_folder):
    compile_command = [ 'latexmk', '-pdf', '-interaction=nonstopmode', f'-jobname={arxiv_id}_tl{texlive_version}', f'-output-directory={output_folder}', tex_file ]
    try:
        stdout_file = os.path.join(logs_folder, f'{arxiv_id}_tl{texlive_version}.out')
        stderr_file = os.path.join(logs_folder, f'{arxiv_id}_tl{texlive_version}.err')
        with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
            proc = subprocess.run(compile_command, timeout=60, stdout=stdout, stderr=stderr, cwd=root)
            return proc.returncode
    except subprocess.TimeoutExpired:
        return 'TIMED_OUT'

def run(texlive_version):
    results = {}
    for arxiv_id in tqdm(os.listdir(EXTRACTED_FOLDER)):
        # create the subdirs for output, if it doesn't exist
        compile_output_folder = os.path.join(VERSION_COMPILED_FOLDER, arxiv_id)
        compile_logs_folder = os.path.join(compile_output_folder, 'logs')
        os.makedirs(compile_output_folder, exist_ok=True)
        os.makedirs(compile_logs_folder, exist_ok=True)
        # run compilation
        for root, _, files in os.walk(os.path.join(EXTRACTED_FOLDER, arxiv_id)):
            tex_file, _, _ = find_entrypoint_file(files, root)
            if tex_file is None: continue
            # if entrypoint is identified, begin compilation
            ret = compile_tex_to_pdf(texlive_version, root, tex_file, compile_logs_folder, arxiv_id, compile_output_folder)
            results[arxiv_id] = ret
            break
        else:
            results[arxiv_id] = 'NO_ENTRYPOINT'
    return results

def save_results(results, texlive_version):
    results_csv_filepath = os.path.join(COMPILE_RESULTS_FOLDER, f'results_{texlive_version}.csv')
    with open(results_csv_filepath, 'w') as csv_file:  
        writer = csv.writer(csv_file)
        for arxiv_id, ret in results.items():
           writer.writerow([arxiv_id, ret])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run text-based comparison (text, formatting, images)')
    parser.add_argument('-ver', required=True, help="texlive version for labelling")
    tl_version = parser.parse_args().ver

    checkpaths(tl_version)
    results = run(tl_version)
    save_results(results, tl_version)

