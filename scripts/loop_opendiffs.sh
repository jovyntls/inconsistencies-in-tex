#!/bin/bash

read arxiv_id
arxiv_id=$(printf %05d $arxiv_id)

open version_cmp/docker_bin_2/diff_pdfs_2020/diff_2306."$arxiv_id"_20_21.pdf

./scripts/loop_opendiffs.sh

