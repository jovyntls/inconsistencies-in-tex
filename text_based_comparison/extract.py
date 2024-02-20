import fitz  # PyMuPDF
from typing import Dict, List, NamedTuple, Set
import hashlib

TEXT_EXTRACTION_FLAGS = (fitz.TEXTFLAGS_DICT \
                        | fitz.TEXT_DEHYPHENATE) \
                        & ~fitz.TEXT_PRESERVE_LIGATURES

class FontInformation(NamedTuple):
    font: str
    flags: int
    color: int
    size: float

class ImageInfo(NamedTuple):
    digest: str
    dimensions: tuple[int, int]

class PdfContent(NamedTuple):
    text: str
    text_with_formatting: Dict[str, str]
    fonts: Set[FontInformation]
    images: List[ImageInfo]

def get_text_fonts_images(pdf_path: str):
    pdf_document = fitz.Document(pdf_path)
    debug_content = []
    full_text, text_with_formatting, fonts_used, images = [], {}, set(), []
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        full_text.append(page.get_text("text", flags=TEXT_EXTRACTION_FLAGS).replace(' ', '\n'))
        images += [ImageInfo( imginfo['digest'], (imginfo['width'], imginfo['height']) ) for imginfo in page.get_image_info(hashes=True)]
        blocks = page.get_text("dict", sort=True, flags=TEXT_EXTRACTION_FLAGS)['blocks']
        # block structure: https://pymupdf.readthedocs.io/en/latest/_images/img-textpage.png
        for block in blocks:
            if block['type'] == 1:   # image block
                debug_content.append(ImageInfo(hashlib.md5(block['image']).hexdigest(), (block['width'], block['height'])))
                continue
            for line in block['lines']:
                for span in line['spans']:
                    font_information = FontInformation(span['font'], span['flags'], span['color'], round(span['size'], 1))
                    fonts_used.add(font_information)
                    debug_content.append( (font_information, span['text']) )
                    if font_information not in text_with_formatting: text_with_formatting[font_information] = []
                    text_with_formatting[font_information].append(span['text'])
    pdf_document.close()
    return PdfContent('\n'.join(full_text), text_with_formatting, fonts_used, images), debug_content
