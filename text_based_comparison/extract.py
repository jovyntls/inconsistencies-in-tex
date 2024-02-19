import fitz  # PyMuPDF
from typing import Dict, List, NamedTuple, Set

TEXT_EXTRACTION_FLAGS = (fitz.TEXTFLAGS_DICT \
                        | fitz.TEXT_DEHYPHENATE) \
                        & ~fitz.TEXT_PRESERVE_LIGATURES

class FontInformation(NamedTuple):
    font: str
    flags: int
    color: int
    size: float

class ImageInfo(NamedTuple):
    image: str
    dimensions: tuple[int, int]

class PdfContent(NamedTuple):
    text: str
    text_with_formatting: Dict[str, str]
    fonts: Set[FontInformation]
    images: List[ImageInfo]

def get_text_fonts_images(pdf_path: str):
    pdf_document = fitz.Document(pdf_path)
    full_text, text_with_formatting, fonts_used, images = [], {}, set(), []
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        full_text.append(page.get_text("text", flags=TEXT_EXTRACTION_FLAGS).replace(' ', '\n'))
        blocks = page.get_text("dict", sort=True, flags=TEXT_EXTRACTION_FLAGS)['blocks']
        # block structure: https://pymupdf.readthedocs.io/en/latest/_images/img-textpage.png
        for block in blocks:
            # image block
            if block['type'] == 1:  
                images.append(ImageInfo( block['image'], (block['width'], block['height']) ))
                continue
            # text block
            for line in block['lines']:
                for span in line['spans']:
                    font_information = FontInformation(span['font'], span['flags'], span['color'], span['size'])
                    fonts_used.add(font_information)
                    if font_information not in text_with_formatting: text_with_formatting[font_information] = []
                    text_with_formatting[font_information].append(span['text'])
    pdf_document.close()
    return PdfContent('\n'.join(full_text), text_with_formatting, fonts_used, images)
