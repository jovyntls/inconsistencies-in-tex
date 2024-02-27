import fitz
from PIL import Image
from config import PROJECT_BIN

def convert_to_imgs(pdf_filepath, pages_to_convert):
    try:
        doc = fitz.Document(pdf_filepath)
    except Exception as err:
        print(f'skipping convert due to error opening file {pdf_filepath}:\n{err}')
        return []
    images = []
    for pagenum, page in enumerate(doc):
        if pagenum+1 not in pages_to_convert: continue
        # save_destination = os.path.join(save_dir, f'{identifier}_pg{pagenum+1}_cmp{page_cmp_id}.jpeg')
        image = page.get_pixmap(dpi=300)
        image = Image.frombytes("RGB", [image.width, image.height], image.samples)
        images.append(image)

    doc.close()
    return images

def highlight_diffs(imgs):
    for img in imgs: 
        data = img.load()
        width, height = img.size
        for x in range(width):
            for y in range(height):
                # skip white pixels
                if data[x, y] == (255,255,255): continue
                r, g, b = data[x, y]
                # if it's the red diff markings, continue
                if x < 12 and r > g and r > b: data[x, y] = (255,255,255)
                # if grayscale (with some buffer), transform to white
                elif abs(r-g) <= 2 and abs(r-b) <= 2: data[x, y] = (255,255,255)
                # else, highlight the diffs
                else: data[x, y] = (255, 0, 0)

def main(arxiv_id, pages_to_convert):
    pdf_path = f'{PROJECT_BIN}/diff_pdfs/diff_2306.{arxiv_id}_xelatex_lualatex.pdf'
    imgs = convert_to_imgs(pdf_path, pages_to_convert)
    highlight_diffs(imgs)
    for img in imgs: img.show()
