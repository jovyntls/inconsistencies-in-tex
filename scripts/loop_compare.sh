#!/bin/bash

read arxiv_id
python3 run_analysis.py -compare $arxiv_id

echo ""
echo ""

./scripts/loop_compare.sh
