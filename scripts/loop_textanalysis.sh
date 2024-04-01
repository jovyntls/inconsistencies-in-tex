#!/bin/bash

read arxiv_id
arxiv_id=$(printf %05d $arxiv_id)
python3 run_text_based_comparison.py -debug -save -id $arxiv_id

echo "---"

./scripts/loop_textanalysis.sh
