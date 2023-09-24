# Differential testing TeX engines

_Automated differential testing on TeX engines (pdfTeX, XeTeX, LuaTeX)_

## Setting up

1. `pip install` the required packages (`requirements.txt`); Python 3.9 required
1. Edit the parameters in `config.py`, minimally the `PROJECT_ROOT`

## Running scripts

All scripts should run from the project root.

### Pipeline

This is the main pipeline (end to end) for differential testing.

To run:

```
python main.py
```

* The run may take a few minutes due to downloading tex files, slow compilations, compilation hangs (timeout 60s), etc.
* Logs and results will be saved in a `logs/` directory under the project root
* Skip steps in the pipeline (e.g. skip downloading if the files already exist) by commenting out the corresponding function call in `main.py`. The required `bin/` folders for each step are specified in `main.py`

### Analysis

Provided as a CLI tool to compare the compiled PDFs from the pipeline (`bin/compiled_tex_pdf/`).

* Compare text and image similarity between PDFs 
    * For all compiled PDFs: `python3 run_analysis.py -compare`
    * For a single arXiv ID (e.g. {YEAR_AND_MONTH}/00002): `python3 run_analysis.py -compare 00002`
    * To save the extracted text and images (all processed) to a .txt file:
        * `python3 run_analysis.py -compare 00002 -save`
* Count the number of pages in _all_ PDFs
    * `python3 run_analysis.py -count`
    * To save the results to a CSV file: `python3 run_analysis.py -count -save`
* Help text: `--help`

---

To ignore config changes:
```
git update-index --skip-worktree config.py
```
(to undo, run `git update-index --no-skip-worktree config.py`)

