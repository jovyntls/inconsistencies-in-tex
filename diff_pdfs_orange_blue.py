from utils.logger import LOGGER
import os
import numpy as np
from pdf2image import convert_from_path
import cv2 as cv
from config import DIFFS_FOLDER

def show_image(img):
    cv.imshow("img", img)
    cv.waitKey(0)
    cv.destroyAllWindows()

def compiled_pdf_filename(COMPILED_FOLDER, engine, arxiv_id):
    return os.path.join(os.path.join(COMPILED_FOLDER, arxiv_id), f'{arxiv_id}_{engine}.pdf')

def pdf_to_img_array(pdf_path):
    images = convert_from_path(pdf_path)
    return [np.array(image)[:, :, ::-1].copy() for image in images]
    # return [cv.cvtColor(np.array(image.convert('HSV')), cv.COLOR_HSV2BGR_FULL) for image in images]

def count_blue_orange_pixels(img):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    total_count = np.size(hsv)
    # openCV uses 0-180 instead of 0-360 for hue
    # orange HSV mask
    orange_lower = np.array([9,0,0])
    orange_upper = np.array([22,255,255])
    orange_mask = cv.inRange(hsv, orange_lower, orange_upper)
    orange_count = np.count_nonzero(orange_mask)
    # blue HSV mask
    blue_lower = np.array([85,0,0])
    blue_upper = np.array([125,255,255])
    blue_mask = cv.inRange(hsv, blue_lower, blue_upper)
    blue_count = np.count_nonzero(blue_mask)
    return ( orange_count / total_count, blue_count / total_count )

def run_opencv_analysis(pdf_diff_file, RESULTS):
    diff_pdf_path = os.path.join(DIFFS_FOLDER, pdf_diff_file)
    LOGGER.debug(f'compare_blue_orange: comparing {pdf_diff_file}')
    pages = pdf_to_img_array(diff_pdf_path)
    res_blue, res_orange = [], []
    for page in pages:
        blue, orange = count_blue_orange_pixels(page)
        res_blue.append(blue)
        res_orange.append(orange)
    arxiv_id, e1, e2 = pdf_diff_file[:-4].split('_')[1:4]
    max_blue, max_orange = max(res_blue), max(res_orange)
    RESULTS.at[arxiv_id, f'{e1[:-5]}<>{e2[:-5]}_B_max'] = max_blue
    RESULTS.at[arxiv_id, f'{e1[:-5]}<>{e2[:-5]}_O_max'] = max_orange
    LOGGER.debug(f'compare_blue_orange: compared {pdf_diff_file}: {max_blue=},\t{max_orange=}')

def main(RESULTS):
    LOGGER.info(f'comparing blue/orange amounts...')
    for pdf_diff_file in os.listdir(DIFFS_FOLDER):
        run_opencv_analysis(pdf_diff_file, RESULTS)
    if 'xe<>lua_B_max' in RESULTS.columns:
        return RESULTS.sort_values(by=['xe<>lua_B_max'], ascending=False)
    elif 'xe<>pdf_B_max' in RESULTS.columns:
        return RESULTS.sort_values(by=['xe<>pdf_B_max'], ascending=False)
    else:
        return RESULTS

