from logger import Log_level
import os
import subprocess
import re

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

def run_tex_engines(project_root, tex_file, logs_folder, arxiv_id, TEX_ENGINES, LOGGER):
    # run all tex engines
    rets = {}
    for tex_engine, run_command in TEX_ENGINES.items():
        try:
            stdout_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.out')
            stderr_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.err')
            with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
                proc = subprocess.run(run_command + [tex_file], timeout=60, stdout=stdout, stderr=stderr, cwd=project_root)
                LOGGER.log(Log_level.DEBUG, f'compile_tex: ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
                rets[tex_engine] = proc
        except subprocess.TimeoutExpired:
            LOGGER.log(Log_level.ERROR, f"compile_tex: timed out for {arxiv_id} [{tex_engine}]")
    return rets

def compare_engine_outputs(rets, COMPILED_FOLDER, DIFFS_FOLDER, arxiv_id, TEX_ENGINES, LOGGER):
    def get_diff_command(e1, e2):
        def output_filename(engine, arxiv_id):
            return os.path.join(os.path.join(COMPILED_FOLDER, arxiv_id), f'{arxiv_id}_{engine}.pdf')
        diff_output = os.path.join(DIFFS_FOLDER, f'diff_{arxiv_id}_{e1}_{e2}.pdf')
        return ['diff-pdf', f'--output-diff={diff_output}', '-smg', '--dpi=100', '--per-page-pixel-tolerance=2000', output_filename(e1, arxiv_id), output_filename(e2, arxiv_id)] 

    # returns bool of whether they match
    def diff_engines(e1, e2):
        try:
            subprocess.run(get_diff_command(e1, e2), check=True)
            LOGGER.log(Log_level.DEBUG, f"[{arxiv_id}] no diffs for [{e1}] <> [{e2}]")
            return True
        except subprocess.CalledProcessError as e:
            LOGGER.log(Log_level.DEBUG, f"diff-pdf: [{arxiv_id}] ret={e.returncode} for [{e1}] <> [{e2}]")
            return False

    if sum([x.returncode for x in rets.values()]) != 0:
        res = '\t'.join([f'{k}={v.returncode}' for k, v in rets.items()])
        LOGGER.log(Log_level.WARN, 'compile failures: ' + f'[{arxiv_id}]' + '\t' + res)
    engines = list(TEX_ENGINES.keys())
    cmp_engine = engines.pop()
    unequal_comparisons = 0
    for tex_engine in engines:
        pdfs_equal = diff_engines(cmp_engine, tex_engine)
        if not pdfs_equal: unequal_comparisons += 1
    return unequal_comparisons

def main(EXTRACTED_FOLDER, COMPILED_FOLDER, DIFFS_FOLDER, LOGGER):
    overall_equal_pdfs = []
    overall_diff_pdfs = []
    LOGGER.log(Log_level.INFO, f'compiling tex files...')
    for arxiv_id in os.listdir(EXTRACTED_FOLDER):
        folder_path = os.path.join(EXTRACTED_FOLDER, arxiv_id)
        output_folder, logs_folder = create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id)
        TEX_ENGINES = {
            'pdflatex': [
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-format=pdf',
                f'-jobname={arxiv_id}_pdflatex',
                f'-output-directory={output_folder}'
            ], 
            'lualatex': [
                'lualatex',
                '--interaction=nonstopmode',
                '--output-format=pdf',
                f'--jobname={arxiv_id}_lualatex',
                f'--output-directory={output_folder}'
            ],
            'xelatex': [
                'xelatex',
                '-interaction=nonstopmode',
                '-output-format=pdf',
                f'-jobname={arxiv_id}_xelatex',
                f'-output-directory={output_folder}'
            ]
        }
        # try to find a tex file
        for root, _, files in os.walk(folder_path):
            tex_file = find_entrypoint_file(files)
            if tex_file is None: 
                LOGGER.log(Log_level.WARN, f'could not find entrypoint tex file: [{arxiv_id}]')
                continue
            LOGGER.log(Log_level.DEBUG, f'found latex file: [{arxiv_id}] {tex_file}')
            # run the tex engines
            rets = run_tex_engines(root, tex_file, logs_folder, arxiv_id, TEX_ENGINES, LOGGER)
            # compare the output pdfs
            unequal_comparisons = compare_engine_outputs(rets, COMPILED_FOLDER, DIFFS_FOLDER, arxiv_id, TEX_ENGINES, LOGGER)
            if unequal_comparisons == 0: overall_equal_pdfs.append(arxiv_id) 
            else: overall_diff_pdfs.append(arxiv_id)
            break
    eqs, diffs = len(overall_equal_pdfs), len(overall_diff_pdfs)
    LOGGER.log(Log_level.INFO, f'compared outputs for {eqs + diffs} papers: {diffs} papers were found with diffs')
    LOGGER.log(Log_level.INFO, f'diffs: {overall_diff_pdfs}')
