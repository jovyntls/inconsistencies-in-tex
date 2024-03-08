import os
import fitz
from config import COMPILED_FOLDER, CONVERTED_IMG_FOLDER, CONVERT_FIRST_N_PAGES, CONVERT_LAST_N_PAGES
from utils.logger import COMPARISON_LOGGER as LOGGER
from utils.tex_engine_utils import TEX_ENGINES, get_engine_name

# returns a list of (page accessor index, page comparison index)
# e.g. [ (0,1), (1,2), (2,3), (18,-3), (19,-2), (20,-1) ]
def get_pages_to_convert(pdf_doc: fitz.Document):
    num_pgs = len(pdf_doc)
    pages_to_convert = []
    if num_pgs < CONVERT_FIRST_N_PAGES + CONVERT_LAST_N_PAGES:
        pages_to_convert = [(i, i+1) for i in range(num_pgs)]
    else:
        first_n_pgs = [(i, i+1) for i in range(CONVERT_FIRST_N_PAGES)]
        last_n_pgs = [(i, idx-CONVERT_LAST_N_PAGES) for idx, i in enumerate(range(num_pgs-CONVERT_LAST_N_PAGES, num_pgs))]
        pages_to_convert = first_n_pgs + last_n_pgs
    return pages_to_convert

def convert_and_save(identifier, pdf_filepath, save_dir):
    try:
        doc = fitz.open(pdf_filepath)
    except Exception as err:
        LOGGER.warn(f'skipping convert due to error opening file {pdf_filepath}:\n{err}')
        return
    # convert images to jpeg and save
    pages_to_convert = get_pages_to_convert(doc)
    LOGGER.debug(f'converting pages for {identifier}: {pages_to_convert} ...')
    for pagenum, page_cmp_id in pages_to_convert:
        page = doc.load_page(pagenum)
        save_destination = os.path.join(save_dir, f'{identifier}_pg{pagenum+1}_cmp{page_cmp_id}.jpeg')
        page.get_pixmap(dpi=200).save(save_destination)
    doc.close()

def main(arxiv_id):  # arxiv_id including YYMM
    # create a subdir for the converted images
    img_subdir = os.path.join(CONVERTED_IMG_FOLDER, arxiv_id)
    if os.path.exists(img_subdir): LOGGER.warn(f'converted_img dir already exists for {arxiv_id} - possible overwrite')
    else: os.makedirs(img_subdir, exist_ok=False)
    # perform conversion for each engine
    for engine in TEX_ENGINES:
        identifier = f'{arxiv_id}_{get_engine_name(engine)}'
        pdf_filepath = os.path.join(COMPILED_FOLDER, arxiv_id, f'{identifier}.pdf')
        if not os.path.exists(pdf_filepath):
            LOGGER.debug(f'{pdf_filepath} not found - skipping')
            continue
        convert_and_save(identifier, pdf_filepath, img_subdir)
