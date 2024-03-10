from collections import namedtuple, Counter
from typing import Dict, List

from utils.logger import ANALYSIS_LOGGER as LOGGER
from text_based_comparison.extract import ImageInfo
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS

THRESHOLD = 0.01  # percentage difference allowed in image dimensions

ImgCmpResult = namedtuple('ImgCmpResult', ['img_correct_order', 'img_num_missing', 'img_num_diff_size'])
def image_comparison(imgs1: List[ImageInfo], imgs2: List[ImageInfo]):
    # check order
    ordered_binaries1 = [img.digest for img in imgs1]
    ordered_binaries2 = [img.digest for img in imgs2]
    is_correct_order = ordered_binaries1 == ordered_binaries2
    # check missing images
    img_counts1 = Counter(ordered_binaries1)
    img_counts2 = Counter(ordered_binaries2)
    missing_images = (img_counts1 - img_counts2) | (img_counts2 - img_counts1)
    if len(missing_images) > 0: 
        LOGGER.debug(f'found {len(missing_images)} missing images')
        pass 
    # check image sizes
    img1_to_dims = {}
    diff_sized_imgs = []
    for img_info in imgs1:
        img, dim = img_info.digest, img_info.dimensions
        if img not in img1_to_dims: img1_to_dims[img] = []
        img1_to_dims[img].append(dim)
    for img_info in reversed(imgs2):
        img, dim2 = img_info.digest, img_info.dimensions
        if img not in img1_to_dims or len(img1_to_dims[img]) == 0: continue
        w1, h1 = img1_to_dims[img].pop()
        w2, h2 = dim2
        min_w, max_w, min_h, max_h = min(w1, w2), max(w1, w2), min(h1, h2), max(h1, h2)
        if min_w == 0 and max_w != 0: diff_sized_imgs.append(img)
        elif min_w > 0 and max_w/min_w > 1+THRESHOLD: diff_sized_imgs.append(img)
        elif min_h == 0 and max_h != 0: diff_sized_imgs.append(img)
        elif min_h > 0 and max_h/min_h > 1+THRESHOLD: diff_sized_imgs.append(img)
    if len(diff_sized_imgs) > 0:
        LOGGER.debug('found {len(diff_sized_imgs)} different-sized images')
        pass
    return ImgCmpResult(is_correct_order, sum(missing_images.values()), len(diff_sized_imgs))

def run_img_comparison(pdf_imgs: Dict[str, List[ImageInfo]]):
    # result_rows_as_dict = { fieldname: { xepdf: 0, xelua: 1 } }
    result_rows_as_dict = { field: {} for field in ImgCmpResult._fields }
    for e1, e2 in DIFF_ENGINE_PAIRS:
        if e1 not in pdf_imgs or e2 not in pdf_imgs: continue
        col = f'{e1}{e2}'
        cmp_result = image_comparison(pdf_imgs[e1], pdf_imgs[e2])
        for fieldname in cmp_result._fields:
            result_rows_as_dict[fieldname][col] = getattr(cmp_result, fieldname)
    result_rows = [ field_result | { 'comparison': fieldname } for fieldname, field_result in result_rows_as_dict.items() ]
    return result_rows

