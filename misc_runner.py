import argparse
from misc import count_pdf_pages, compare_text_similarity

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run misc scripts')
    parser.add_argument('-save', action='store_true', help="save results to a file")
    parser.add_argument('-count', action='store_true', help="count the number of pages for ALL pdfs")
    parser.add_argument('-compare', type=str, help="arxiv_id to compare text")
    args = parser.parse_args()
    if args.count:
        count_pdf_pages.main(should_save=args.save)
    if args.compare:
        compare_text_similarity.main(args.compare)
        if args.save:
            compare_text_similarity.extract_pdf_text_to_save_file(args.compare)
