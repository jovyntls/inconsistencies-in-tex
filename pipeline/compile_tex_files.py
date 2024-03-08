from utils.tex_engine_utils import get_compile_tex_commands, get_engine_name
from utils.logger import PIPELINE_LOGGER as LOGGER
from constants.engine_primitives import PDFTEX_PRIMITIVES, PDFTEX_CHECK
import os
import subprocess
import re
import pandas as pd

"""Identify the documentclass of a file. Returns (documentclass, params)"""
DOCUMENTCLASS_REGEX = re.compile(r'(?:^|\n)\s*\\documentclass(?P<params>\[(?:.*?\n?)*?\])?\s*?{(?P<docclass>.+)}')
def get_documentclass(file_path):
    with open(file_path, errors='ignore') as f:
        file_content = f.read()
        result = DOCUMENTCLASS_REGEX.search(file_content)
        if result == None: return None, None
        if result.group('docclass') == None or result.group('params') == None: return result.group('docclass'), result.group('params')
        params_cleaned = filter(lambda s: s[0] != '%', [s.strip() for s in result.group('params').split('\n')])
        return result.group('docclass'), ''.join(params_cleaned)

"""Find the entrypoint tex file for compilation"""
def find_entrypoint_file(files, root):
    def return_file_with_docclass(file):
        if file == None: return None, None, None
        file_path = os.path.join(root, file)
        docclass, params = get_documentclass(file_path)
        return file, docclass, params

    # 0. check if it is a single uncompressed tex file
    for file in files:
        # ideally check len(files)==1, but not always true since aux files will be there if code is rerun
        if re.search(r'\d{4}\.\d+', file) is not None:
            return return_file_with_docclass(file)
    # 1. match any entrypoint
    ENTRYPOINT_EXACT_MATCH = { 'main.tex', 'manuscript.tex', 'mainnew.tex' }
    # 2. eliminate non-tex files and blacklisted files
    TEX_FILE_EXTENSION = 'tex'
    FILE_BLACKLIST_EXACT = ['math_commands.tex', 'commands.tex', 'macros.tex']
    FILE_BLACKLIST_REGEX = [r'.*shorthands.*\.tex$', r'.*math_commands.*\.tex$', r'.*macros.*\.tex$', r'.*preamble.*\.tex$', r'.*declarations.*\.tex$', r'.*notation.*\.tex$']
    FILE_BLACKLIST_REGEX = [re.compile(s, re.IGNORECASE) for s in FILE_BLACKLIST_REGEX]
    # 3. fuzzy match these, followed by any file ending in tex
    ENTRYPOINT_REGEXES = [ r'main.*\.tex$', r'.*arxiv.*\.tex$', r'.*paper.*\.tex$', r'.*final.*\.tex$',  r'.*2023.*\.tex$', r'.*\.tex$' ]
    ENTRYPOINT_REGEXES  = [re.compile(s, re.IGNORECASE) for s in ENTRYPOINT_REGEXES]

    # 1. exact match for any entrypoint
    exact_matches = ENTRYPOINT_EXACT_MATCH.intersection(files)
    if len(exact_matches) > 0:
        file = list(exact_matches)[0]
        return return_file_with_docclass(file)
    # 2. eliminate blacklisted files and non-tex files
    ok_files = []
    for file in files:
        if not file.endswith(TEX_FILE_EXTENSION): continue
        if file in FILE_BLACKLIST_EXACT: continue
        for pattern in FILE_BLACKLIST_REGEX:
            if pattern.search(file): break
        else: ok_files.append(file)
    # 3. look for a reasonable file that has a documentclass
    for pattern in ENTRYPOINT_REGEXES:
        for file in ok_files:
            match = pattern.search(file)
            if not match: continue
            # a valid entrypoint should have a documentclass
            file, docclass, params = return_file_with_docclass(file)
            if docclass == None: continue
            return file, docclass, params
    return return_file_with_docclass(None)

def create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id):
    output_folder = os.path.join(COMPILED_FOLDER, arxiv_id)
    logs_folder = os.path.join(output_folder, 'logs')
    os.makedirs(output_folder, exist_ok=False)
    os.makedirs(logs_folder, exist_ok=False)
    return output_folder, logs_folder

def run_tex_engines(project_root, tex_file, logs_folder, arxiv_id, output_folder):
    # run all tex engines
    COMPILE_TEX_COMMANDS = get_compile_tex_commands(arxiv_id, output_folder)
    rets = {}
    for tex_engine, run_command in COMPILE_TEX_COMMANDS.items():
        try:
            engine_name = get_engine_name(tex_engine)
            stdout_file = os.path.join(logs_folder, f'{arxiv_id}_{engine_name}.out')
            stderr_file = os.path.join(logs_folder, f'{arxiv_id}_{engine_name}.err')
            with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
                cmd = run_command + [tex_file]
                # compile
                proc = subprocess.run(cmd, timeout=60, stdout=stdout, stderr=stderr, cwd=project_root)
                LOGGER.debug(f'compile_tex (1): ret={proc.returncode} for {arxiv_id} [{engine_name}]')
                rets[tex_engine] = proc.returncode
                # log if the compile failed
                if proc.returncode != 0: LOGGER.warning(f'compile_tex: ret={proc.returncode} for {arxiv_id} [{engine_name}]')
        except subprocess.TimeoutExpired:
            LOGGER.error(f"compile_tex: timed out for {arxiv_id} [{tex_engine}]")
    return rets

"""Remove engine-specific commands"""
def process_file(file, arxiv_id):
    LOGGER.debug(f'processing files for engine-specific primitives...')
    lines = []
    lines_removed = []
    with open(file, 'r', errors='ignore') as fp:
        lines = fp.readlines()
    with open(file, 'w', errors='ignore') as fp:
        for line in lines:
            if PDFTEX_CHECK not in line: fp.write(line)  # quick optimisation to avoid iterating
            else:
                should_keep_line = True
                for primitive in PDFTEX_PRIMITIVES:
                    if primitive in line: 
                        should_keep_line = False
                        lines_removed.append(line)
                        break
                if should_keep_line: fp.write(line)
    if len(lines_removed) == 0: LOGGER.debug(f'process engine primitives: no lines removed for {arxiv_id}')
    else: LOGGER.debug(f'process engine primitives: removed {len(lines_removed)} for {arxiv_id}. {lines_removed}')
    return

def main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS):
    LOGGER.info('compiling tex files...')
    results_to_concat = []
    for arxiv_id in os.listdir(EXTRACTED_FOLDER):
        folder_path = os.path.join(EXTRACTED_FOLDER, arxiv_id)
        output_folder, logs_folder = create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id)
        # try to find a tex file
        for root, _, files in os.walk(folder_path):
            tex_file, docclass, docclass_params = find_entrypoint_file(files, root)
            if tex_file is None: 
                LOGGER.warning(f'could not find entrypoint tex file: [{arxiv_id}]')
                continue
            LOGGER.debug(f'found latex file: [{arxiv_id}] {tex_file}')
            # skip compiles for some files 
            file_path = os.path.join(root, tex_file)
            # make the file engine-agnostic
            process_file(file_path, arxiv_id)
            # run the tex engines
            rets = run_tex_engines(root, tex_file, logs_folder, arxiv_id, output_folder)
            # convert to a new df row
            rets['arxiv_id'] = arxiv_id
            rets['entrypoint'] = tex_file
            rets['documentclass'] = docclass
            rets['docclass_params'] = docclass_params
            results_to_concat.append(rets)
            break
    RESULTS = pd.concat([RESULTS, pd.DataFrame.from_records(results_to_concat, index='arxiv_id')])
    LOGGER.info(f'compiled {len(RESULTS.index)} papers.')
    LOGGER.debug(RESULTS)
    return RESULTS
