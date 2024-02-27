import argparse
from img_comparison import highlight_diffs

if __name__ == '__main__':
    # e.g. python3 run_diff_highlight.py -id 00207 -pg 1 2 3
    parser = argparse.ArgumentParser(description='Highlight diffs in a diff-pdf')
    parser.add_argument('-id', required=True, help="arxiv_id to run on")
    parser.add_argument('-pg', required=True, nargs='+', help="pages to run on")
    args = parser.parse_args()

    pages = [int(x) for x in args.pg]
    highlight_diffs.main(args.id, pages)
