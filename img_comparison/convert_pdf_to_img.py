import os
import fitz
from config import COMPILED_FOLDER, CONVERTED_IMG_FOLDER, CONVERT_FIRST_N_PAGES, CONVERT_LAST_N_PAGES
from utils.logger import COMPARISON_LOGGER as LOGGER
from utils.tex_engine_utils import TEX_ENGINES

def convert_and_save(identifier, pdf_filepath, save_dir):
    doc = fitz.open(pdf_filepath)
    # convert images to jpeg and save
    num_pgs = len(doc)
    pages_to_convert = []
    if num_pgs < CONVERT_FIRST_N_PAGES + CONVERT_LAST_N_PAGES:
        pages_to_convert = list(range(num_pgs))
    else:
        first_n_pgs = list(range(CONVERT_FIRST_N_PAGES))
        last_n_pgs = list(range(num_pgs-1-CONVERT_LAST_N_PAGES, num_pgs-1))
        pages_to_convert = first_n_pgs + last_n_pgs
    LOGGER.debug(f'converting pages for {identifier}: {pages_to_convert} ...')
    for pagenum in pages_to_convert:
        page = doc.load_page(pagenum)
        save_destination = os.path.join(save_dir, f'{identifier}_pg{pagenum+1}.jpeg')
        page.get_pixmap(dpi=150).save(save_destination)
    doc.close()

def main(arxiv_id):  # arxiv_id including YYMM
    # create a subdir for the converted images
    img_subdir = os.path.join(CONVERTED_IMG_FOLDER, arxiv_id)
    if os.path.exists(img_subdir): LOGGER.warn(f'converted_img dir already exists for {arxiv_id} - possible overwrite')
    else: os.makedirs(img_subdir, exist_ok=False)
    # perform conversion for each engine
    for engine in TEX_ENGINES:
        identifier = f'{arxiv_id}_{engine}'
        pdf_filepath = os.path.join(COMPILED_FOLDER, arxiv_id, f'{identifier}.pdf')
        if not os.path.exists(pdf_filepath):
            LOGGER.debug(f'{pdf_filepath} not found - skipping')
            continue
        convert_and_save(identifier, pdf_filepath, img_subdir)
