from utils import tex_engine_utils
from utils.logger import LOGGER
from config import SHOULD_SKIP_COMPILE, SKIP_COMPILE_FOR
from constants.engine_primitives import PDFTEX_PRIMITIVES, PDFTEX_CHECK
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
    ENTRYPOINT_REGEXES = [ r'main.*\.tex$', r'.*arxiv.*\.tex$', r'.*paper.*\.tex$', r'.*final.*\.tex$',  r'.*2023.*\.tex$', r'.*\.tex$' ]
    # 3. use any reasonable .tex file
    FILE_BLACKLIST = ['math_commands.tex', 'commands.tex', 'macros.tex']
    FILE_BLACKLIST_REGEX = [r'.*shorthands.*\.tex$', r'.*math_commands.*\.tex$', r'.*macros.*\.tex$', r'.*preamble.*\.tex$', r'.*declarations.*\.tex$', r'.*notation.*\.tex$']
    FILE_BLACKLIST_REGEX = [re.compile(s) for s in FILE_BLACKLIST_REGEX]

    exact_matches = ENTRYPOINTS.intersection(files)
    if len(exact_matches) > 0:
        return list(exact_matches)[0]
    # remove blacklisted files
    ok_files = []
    for file in files:
        if file in FILE_BLACKLIST: continue
        should_blacklist = False
        for pattern in FILE_BLACKLIST_REGEX:
            if pattern.search(file): 
                should_blacklist = True
                break
        if not should_blacklist: ok_files.append(file)
    # look for a reasonable file
    for pattern in ENTRYPOINT_REGEXES:
        for file in ok_files:
            match = re.search(pattern, file, re.IGNORECASE)
            if match: return file
    return None

def create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id):
    output_folder = os.path.join(COMPILED_FOLDER, arxiv_id)
    logs_folder = os.path.join(output_folder, 'logs')
    os.makedirs(output_folder, exist_ok=False)
    os.makedirs(logs_folder, exist_ok=False)
    return output_folder, logs_folder

def run_tex_engines(project_root, tex_file, logs_folder, arxiv_id, output_folder):
    # run all tex engines
    COMPILE_TEX_COMMANDS = tex_engine_utils.get_compile_tex_commands(arxiv_id, output_folder)
    rets = {}
    for tex_engine, run_command in COMPILE_TEX_COMMANDS.items():
        try:
            stdout_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.out')
            stderr_file = os.path.join(logs_folder, f'{arxiv_id}_{tex_engine}.err')
            with open(stdout_file, 'w') as stdout, open(stderr_file, 'w') as stderr:
                cmd = run_command + [tex_file]
                # compile
                proc = subprocess.run(cmd, timeout=60, stdout=stdout, stderr=stderr, cwd=project_root)
                LOGGER.debug(f'compile_tex (1): ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
                rets[tex_engine] = proc.returncode
                # log if the compile failed
                if proc.returncode != 0: LOGGER.warning(f'compile_tex: ret={proc.returncode} for {arxiv_id} [{tex_engine}]')
        except subprocess.TimeoutExpired:
            LOGGER.error(f"compile_tex: timed out for {arxiv_id} [{tex_engine}]")
    return rets

"""Identify the documentclass of a file. Returns (documentclass, params)"""
DOCUMENTCLASS_REGEX = re.compile(r'(?:^|\n)\s*\\documentclass(?P<params>\[(?:.*?\n?)*?\])?\s*?{(?P<docclass>.+)}')
def get_documentclass(file):
    with open(file, errors='ignore') as f:
        file_content = f.read()
        result = DOCUMENTCLASS_REGEX.search(file_content)
        if result == None: return None, None
        if result.group('docclass') == None or result.group('params') == None: return result.group('docclass'), result.group('params')
        params_cleaned = filter(lambda s: s[0] != '%', [s.strip() for s in result.group('params').split('\n')])
        return result.group('docclass'), ''.join(params_cleaned)

"""Skip compiles for files containing keywords specified in config.py"""
def should_skip_compile(tex_file, arxiv_id):
    # if the skip compile flag is off, don't skip
    if SHOULD_SKIP_COMPILE == False: return False
    # else, check if the file should be skipped
    with open(tex_file, errors='ignore') as f:
        file_content = f.read()
        for keyword in SKIP_COMPILE_FOR:
            if keyword in file_content: 
                LOGGER.debug(f'skipping file: [{arxiv_id}] {tex_file} uses {keyword}')
                return True
    return False

"""Remove engine-specific commands"""
def process_file(file):
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
    if len(lines_removed) == 0: LOGGER.debug(f'process_file: no lines removed for {file}')
    else: LOGGER.debug(f'process_file: removed for {file}: {lines_removed}')
    return

def main(EXTRACTED_FOLDER, COMPILED_FOLDER, RESULTS):
    LOGGER.info('compiling tex files...')
    skipped_files = []
    results_to_concat = []
    for arxiv_id in os.listdir(EXTRACTED_FOLDER):
        folder_path = os.path.join(EXTRACTED_FOLDER, arxiv_id)
        output_folder, logs_folder = create_output_and_log_dirs(COMPILED_FOLDER, arxiv_id)
        # try to find a tex file
        for root, _, files in os.walk(folder_path):
            tex_file = find_entrypoint_file(files)
            if tex_file is None: 
                LOGGER.warning(f'could not find entrypoint tex file: [{arxiv_id}]')
                continue
            LOGGER.debug(f'found latex file: [{arxiv_id}] {tex_file}')
            # skip compiles for some files 
            file_path = os.path.join(root, tex_file)
            if should_skip_compile(file_path, arxiv_id): 
                skipped_files.append(f'{arxiv_id}/{tex_file}')
                break
            # get documentclass
            docclass = get_documentclass(file_path)
            # make the file engine-agnostic
            process_file(file_path)
            # run the tex engines
            rets = run_tex_engines(root, tex_file, logs_folder, arxiv_id, output_folder)
            # convert to a new df row
            rets['arxiv_id'] = arxiv_id
            rets['entrypoint'] = tex_file
            rets['documentclass'] = docclass[0]
            rets['docclass_params'] = docclass[1]
            results_to_concat.append(rets)
            break
    RESULTS = pd.concat([RESULTS, pd.DataFrame.from_records(results_to_concat, index='arxiv_id')])
    LOGGER.info(f'compiled: {len(RESULTS.index)} papers.\tskipped: {len(skipped_files)} papers.')
    LOGGER.debug(f'skipped {len(skipped_files)} papers: {skipped_files}')
    LOGGER.debug(RESULTS)
    return RESULTS
