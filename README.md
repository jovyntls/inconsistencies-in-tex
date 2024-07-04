# Differential testing TeX software

_Automated differential testing pipeline for TeX engines and TeX Live distributions_

## Getting Started

### Requirements

* Python 3.9
* [diff-pdf](https://github.com/vslavik/diff-pdf)
* A Python environment with the required packages (`pip install -r requirements.txt`)

### Set up

1. Edit the parameters in `config.py`, minimally the `PROJECT_ROOT`
1. Edit `TEX_ENGINES`, `DIFF_ENGINE_PAIRS`, and `TEX_ENGINES_NAMES` in `utils/tex_engine_utils.py` depending on whether the run is to compare PDFTeX/XeTeX/LuaTeX or different versions of TeX Live. _Either_ lines 1-3 _or_ lines 5-7 should be commented out.

Dockerfiles with different TeX Live distributions can be found in `version_cmp/`.

## Running scripts

All scripts should run from the project root.

### Pipeline

This is the main automated pipeline (end to end) for identifying inconsistencies.

To run:

```
python main.py
```

* The run may take a few minutes due to downloading tex files, slow compilations, compilation hangs (timeout 60s), etc.
* Logs and results will be saved in a `logs/` directory under the project root
* Skip steps in the pipeline (e.g. skip downloading if the files already exist) by commenting out the corresponding function call in `main.py`. The required `bin/` folders for each step are specified in `main.py`

### Analysis

Provided as a CLI tool to compare one or all compiled PDFs from the pipeline. 
The PDFs are read from the {COMPILED_FOLDER} and {YEAR_AND_MONTH} variables in `config.py`

* Compare text and image similarity between PDFs 
    * `python3 run_analysis.py -compare` for all compiled PDFs
    * `python3 run_analysis.py -compare 00002` for the arXiv ID {YEAR_AND_MONTH}.00002
        * `python3 run_analysis.py -compare 00002 -save` will also save the extracted text and images (all processed) to a .txt file
* Count the number of pages in _all_ PDFs
    * `python3 run_analysis.py -count-pages`
    * `python3 run_analysis.py -count-pages -save` to save the results to a CSV file
* Count the number of compiled PDFs in for each engine
    * `python3 run_analysis.py -count-compiled`
    * `python3 run_analysis.py -count-compiled -save` to save the results to a CSV file
* Help text: `--help`

### Comparison Pipeline

This directory implements similarity comparison on PDF files through the following steps:

1. Convert the PDF to an image
1. Run the image comparison algorithm(s) on equivalent images.

The PDFs are read from {SOURCE_PDF_FOLDER} and converted to images in {CONVERTED_IMG_FOLDER}.

* Run the comparison pipeline:
    * `python3 run_img_comparison.py -id 00002` for the arXiv ID {YEAR_AND_MONTH}.00002
    * `python3 run_img_comparison.py`

### Text-based comparison

This directory implements comparison based on extracting data from the PDF using PyMuPDF.
This includes text, fonts, and images.

* Run text-based comparison
    * `python3 run_text_based_comparison.py` for all PDFs in the compiled bin folder, or the IDs specified in {DOWNLOAD_BY_ARXIV_IDS}
    * `python3 run_text_based_comparison.py -id 01234` for the specified arXiv ID {YEAR_AND_MONTH}.01234
* Additional flags
    * `-debug` will add debug information
    * `-save` will save the extracted information to a .txt file

### Others

* Highlight the differences between two PDFs
    * `python3 run_diff_highlight.py -id 01308 -pg 1 3 5` for the arXiv ID {YEAR_AND_MONTH}.01308 on pages 1,3,5
* Count and compare number of runs of `latexmk`
    * `python3 count_latexmk_runs.py`
* Run compilation only
    * `python3 run_compile_only.py -ver 2023` to run compilation for TL2023 (to be run inside a docker containing with TL2023)
    * `python3 run_compile_only.py -ver 2020 -flags` to run compilation with additional compile flags (for TL2020)


---

To ignore config changes:
```
git update-index --skip-worktree config.py
```
(to undo, run `git update-index --no-skip-worktree config.py`)

