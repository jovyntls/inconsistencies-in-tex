import os
from typing import Dict, List, Set
from tqdm import tqdm
from config import COMPILED_FOLDER, COMPILED_FOLDER_2020
import re
import pandas as pd
import csv
from collections import Counter

def get_2122cmp_results() -> tuple[Dict[str, bool], Dict[str, bool]]:
    cmp_results = {}
    refs_inconsistent = {}
    with open('/Users/jovyntan/Desktop/2122cmp.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            arxiv_id = row[0]
            cmp_results[arxiv_id] = row[1] == 'TRUE'
            refs_inconsistent[arxiv_id] = row[3] == '1'
    return cmp_results, refs_inconsistent

def count_latexmk_rule_runs() -> tuple[
        Dict[str, Dict[str, int]],  # number_of_runs = { '2020': 1, '2021': 2, ... }
        Dict[str, Dict[str, List[str]]],  # named_runs = { '2020': ['pdftex', 'bibtex'], '2021': ... }
        Dict[str, Dict[str, int]]  # number_of_bibtex_errors = { '2020': 1, '2021': 2, ... }
    ]:
    RUNNING_RULE_PATTERN_2020 = re.compile(r"Latexmk: applying rule '(.+)'...")
    RUNNING_RULE_PATTERN = re.compile(r"------------\s*\n\s*Run number \d+ of rule '(.+)'")
    BIBTEX_ERRORS_PATTERN = re.compile(r"\(There were (\d+) error messages\)")
    print('running for 2020')
    number_of_runs = {}
    named_runs = {}
    number_of_bibtex_errors = {}
    for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER_2020)):
        # count rule runs
        logfile = os.path.join(COMPILED_FOLDER_2020, arxiv_id, 'logs', f'{arxiv_id}_tl2020.out')
        if not os.path.isfile(logfile): continue
        with open(logfile, 'rb') as file:
            text = file.read().decode('latin-1')
            matches = RUNNING_RULE_PATTERN_2020.findall(text)
            number_of_runs[arxiv_id] = { '2020': len(matches) }
            named_runs[arxiv_id] = { '2020': [s.split(' ')[0] for s in matches] }
        # count bibtex errors
        biblogfile = os.path.join(COMPILED_FOLDER_2020, arxiv_id, f'{arxiv_id}_tl2020.blg')
        if not os.path.isfile(biblogfile): continue
        with open(biblogfile, 'rb') as file:
            text = file.read().decode('latin-1')
            matches = BIBTEX_ERRORS_PATTERN.findall(text)
            if len(matches) > 1: print(f'multiple bibtex matches found for {arxiv_id}: ', matches)
            number_of_bibtex_errors[arxiv_id] = { '2020': 0 if len(matches) == 0 else int(matches[0]) }
    print('running for 2021, 2022, 2023')
    for arxiv_id in tqdm(os.listdir(COMPILED_FOLDER)):
        for year in [ '2021', '2022', '2023' ]:
            # count rule runs
            logfile = os.path.join(COMPILED_FOLDER, arxiv_id, 'logs', f'{arxiv_id}_tl{year}.out')
            if not os.path.isfile(logfile): continue
            with open(logfile, 'rb') as file:
                text = file.read().decode('latin-1')
                matches = RUNNING_RULE_PATTERN.findall(text)
                if arxiv_id not in number_of_runs: number_of_runs[arxiv_id] = {}
                number_of_runs[arxiv_id][year] = len(matches)
                if arxiv_id not in named_runs: named_runs[arxiv_id] = {}
                named_runs[arxiv_id][year] = [s.split(' ')[0] for s in matches]
            # count bibtex errors
            biblogfile = os.path.join(COMPILED_FOLDER, arxiv_id, f'{arxiv_id}_tl{year}.blg')
            if not os.path.isfile(biblogfile): continue
            with open(biblogfile, 'rb') as file:
                text = file.read().decode('latin-1')
                matches = BIBTEX_ERRORS_PATTERN.findall(text)
                if arxiv_id not in number_of_bibtex_errors: number_of_bibtex_errors[arxiv_id] = {}
                if len(matches) > 1: print(f'multiple bibtex matches found for {arxiv_id}: ', matches)
                number_of_bibtex_errors[arxiv_id][year] = 0 if len(matches) == 0 else int(matches[0])
    return number_of_runs, named_runs, number_of_bibtex_errors

def collate(number_of_runs: Dict[str, Dict[str, int]]) -> Dict[str, Set[str]]:
    results = {
        'all equal': set(),
        'all diff': set(),
        '21 < 22 = 23': set(),
        '21 > 22 = 23': set(),
        '21 = 22 < 23': set(),
        '21 = 22 > 23': set(),
        'others': set()
    }
    for arxiv_id, data in number_of_runs.items():
        run21, run22, run23 = data['2021'], data['2022'], data['2023']
        if run21 == run22 == run23: results['all equal'].add(arxiv_id)
        elif run21 != run22 and run22 != run23 and run21 != run23: results['all diff'].add(arxiv_id)
        elif run21 < run22 and run22 == run23: results['21 < 22 = 23'].add(arxiv_id)
        elif run21 > run22 and run22 == run23: results['21 > 22 = 23'].add(arxiv_id)
        elif run21 == run22 and run22 < run23: results['21 = 22 < 23'].add(arxiv_id)
        elif run21 == run22 and run22 > run23: results['21 = 22 > 23'].add(arxiv_id)
        else: results['others'].add(arxiv_id)
    for k, v in results.items():
        print(f'{k}: \t{len(v)}')
    return results

def testing_hypothesis(collated_num_runs, number_of_bibtex_errors, named_runs, cmp_results_2122, inconsistent_refs_2122):
    print('---------------------')
    print('HYPOTHESIS: latexmk runs [21 > 22 = 23] because of bibtex errors')
    different_pdfs = {'bibtex_error': set(), 'no_error': set(), 'no_blg_file': set()}
    identical_pdfs = {'bibtex_error': set(), 'no_error': set(), 'no_blg_file': set()}
    different_pdfs_refs  = {'identical': set(), 'different': set()}
    for arxiv_id in collated_num_runs['21 > 22 = 23']:
        if not cmp_results_2122[arxiv_id]: different_pdfs_refs['different' if inconsistent_refs_2122[arxiv_id] else 'identical'].add(arxiv_id)
        result_dict = identical_pdfs if cmp_results_2122[arxiv_id] else different_pdfs
        if arxiv_id not in number_of_bibtex_errors:
            result_dict['no_blg_file'].add(arxiv_id)
        elif number_of_bibtex_errors[arxiv_id] == 0:
            result_dict['no_error'].add(arxiv_id)
        else:
            result_dict['bibtex_error'].add(arxiv_id)
    print(f"total: \t{len(collated_num_runs['21 > 22 = 23'])}")
    print(f">>> identical PDFs: \t{sum([ len(a) for a in identical_pdfs.values() ])}")
    for k, v in identical_pdfs.items():
        print(f'{k}: \t{len(v)}')
    print(f">>> different PDFs: \t{sum([ len(a) for a in different_pdfs.values() ])} \t(refs: {len(different_pdfs_refs['identical'])} identical, {len(different_pdfs_refs['different'])} different)")
    for k, v in different_pdfs.items():
        print(f'{k}: \t{len(v)}')
    print('----- SHOWN: the majority of different PDFs where [21 > 22 = 23] contain bibtex errors')
    print('---------------------')
    print('HYPOTHESIS: inconsistent references are caused by latexmk halting after bibtex error')
    latexmk_2022_last_rule = {}
    bibtex_runs_2021_minus_2022 = {}
    for arxiv_id in different_pdfs['bibtex_error']:
        last_rule_2022 = named_runs[arxiv_id]['2022'][-1]
        bibtex_diff = named_runs[arxiv_id]['2021'].count('bibtex') - named_runs[arxiv_id]['2022'].count('bibtex')
        if last_rule_2022 not in latexmk_2022_last_rule: latexmk_2022_last_rule[last_rule_2022] = set()
        if bibtex_diff not in bibtex_runs_2021_minus_2022: bibtex_runs_2021_minus_2022[bibtex_diff] = set()
        latexmk_2022_last_rule[last_rule_2022].add(arxiv_id)
        bibtex_runs_2021_minus_2022[bibtex_diff].add(arxiv_id)
    print('for PDFs with bibtex errors and inconsistent refs,')
    print('\tlast rules of latexmk 2022:', { k: len(v) for k, v in latexmk_2022_last_rule.items() })
    print('\tbibtex runs in 2021 minus 2022:', { k: len(bibtex_runs_2021_minus_2022[k]) for k in sorted(bibtex_runs_2021_minus_2022.keys()) })
    print('these contradict the hypothesis:', bibtex_runs_2021_minus_2022[0])
    print('control: identical PDFs')
    print('\tbibtex runs in 2021 minus 2022 (with bibtex errors):', dict(Counter([ named_runs[arxiv_id]['2021'].count('bibtex') - named_runs[arxiv_id]['2022'].count('bibtex') for arxiv_id in identical_pdfs['bibtex_error'] ])))
    print('\tbibtex runs in 2021 minus 2022 (no .blg file):', dict(Counter([ named_runs[arxiv_id]['2021'].count('bibtex') - named_runs[arxiv_id]['2022'].count('bibtex') for arxiv_id in identical_pdfs['no_blg_file'] ])))
    print('\tall runs in 2021 minus 2022 (with bibtex errors):', dict(Counter([ len(named_runs[arxiv_id]['2021']) - len(named_runs[arxiv_id]['2022']) for arxiv_id in identical_pdfs['bibtex_error'] ])))
    print('\tall runs in 2021 minus 2022 (no .blg file):', dict(Counter([ len(named_runs[arxiv_id]['2021']) - len(named_runs[arxiv_id]['2022']) for arxiv_id in identical_pdfs['no_blg_file'] ])))
    print('----- SHOWN: for documents with bibtex errors, most of the time, 2022 runs fewer times')
    print('FINAL HYPOTHESIS: ')
    print('thus the 21<>22 reference issue is due to latexmk not calling bibtex enough times, and can be fixed by calling bibtex again')
    print('TODO: (1) copy the version_cmp/docker_bin_2/version_compiled_pdf with the aux files, (2) run bibtex again, (3) see if ref issues disappear')



if __name__ == '__main__':
    cmp_results_2122, inconsistent_refs_2122 = get_2122cmp_results()
    number_of_runs, named_runs, number_of_bibtex_errors = count_latexmk_rule_runs()
    collated_num_runs = collate(number_of_runs)
    testing_hypothesis(collated_num_runs, number_of_bibtex_errors, named_runs, cmp_results_2122, inconsistent_refs_2122)



