#!/bin/bash

read arxiv_id
arxiv_id=$(printf %05d $arxiv_id)

open version_cmp/docker_bin_2/diff_pdfs_2020/diff_2306."$arxiv_id"_20_23.pdf
python3 run_text_based_comparison.py -debug -save -id $arxiv_id

echo ""
echo "************** [$arxiv_id] completed **************"

./scripts/loop_opendiffs_textanalysis.sh



