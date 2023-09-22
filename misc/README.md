quick scripts to analyse the results of the differential testing pipeline

---

## Running

Run the `misc_runner.py` program from the project root (including the `requirements.txt`); run with `--help` flag for details.

### Examples

* Compare text similarity between PDFs from arXiv ID 2306.00002:
    * `python3 misc_runner.py -compare 00002`
    * To save the extracted and processed text to a .txt file:
        * `python3 misc_runner.py -compare 00002 -save`
* Count the number of pages in ALL PDFs
    * `python3 misc_runner.py -count`
    * To save the results to a CSV file: `python3 misc_runner.py -count -save`

