import os
import cv2
from PIL import Image
from skimage.metrics import structural_similarity
import ssim.ssimlib as pyssim
from config import CONVERTED_IMG_FOLDER
from utils.logger import COMPARISON_LOGGER as LOGGER
from utils.tex_engine_utils import TEX_ENGINES

SIM_IMAGE_SIZE = (1295, 1000)  # height*width. roughly a4 paper dimensions

# comparison algos
CMP_ALGORITHMS = {
    'SSIM': lambda i1,i2: { 'SSIM': structural_similarity(i1,i2) },
    'CWSSIM': lambda i1,i2: { 'CWSSIM': pyssim.SSIM(Image.fromarray(i1)).cw_ssim_value(Image.fromarray(i2)) },
    'ORB': lambda i1,i2: compare_with_score_calculation(i1, i2, 'ORB'),
    'SIFT': lambda i1,i2: compare_with_score_calculation(i1, i2, 'SIFT'),
}
CMP_ALGO_THRESHOLDS = {
    'SSIM': 0.7,
    'CWSSIM': 0.7,
    'ORB': 0.7,
    'SIFT': 0.7,
}
assert(CMP_ALGORITHMS.keys() == CMP_ALGO_THRESHOLDS.keys())

def compare_with_score_calculation(img1, img2, cmp_method):
    result = {}
    ALGOS = {
        'ORB': cv2.ORB_create(nfeatures=1000),
        'SIFT': cv2.SIFT_create(nfeatures=1000),
    }
    ALGO_NORM_METHODS = { 'ORB': cv2.NORM_HAMMING, 'SIFT': cv2.NORM_L1 }
    assert(cmp_method in ALGOS and cmp_method in CMP_ALGO_THRESHOLDS and cmp_method in ALGO_NORM_METHODS)
    # Read imgs and compare
    cmp_algo = ALGOS[cmp_method]
    kps1, des1 = cmp_algo.detectAndCompute(img1,None)
    kps2, des2 = cmp_algo.detectAndCompute(img2,None)
    num_kps1, num_kps2 = len(kps1), len(kps2)
    # initialise BFMatcher
    bf = cv2.BFMatcher(normType=ALGO_NORM_METHODS[cmp_method], crossCheck=True)
    # matches = bf.knnMatch(des1,des2, k=2)
    # similarity_count = sum([ m.distance < ALGO_RATIOS[cmp_method] * n.distance for m,n in matches ])
    matches = bf.match(des1,des2)
    similarity_count = len(matches)
    result[f'{cmp_method}_minkps'], result[f'{cmp_method}_maxkps'] = min(num_kps1, num_kps2), max(num_kps1, num_kps2)
    if num_kps1 == 0 and num_kps2 == 0:
        if len(matches) == 0:
            result[cmp_method] = 1
            result[f'{cmp_method}_MAX'] = 1
        else:
            LOGGER.warn(f'no keypoints found for both images but matches were found')
            result[cmp_method] = -1
            result[f'{cmp_method}_MAX'] = -1
    else:
        result[f'{cmp_method}_MAX'] = similarity_count/max(num_kps1, num_kps2)
        if num_kps1 == 0 or num_kps2 == 0:
            result[cmp_method] = similarity_count/max(num_kps1, num_kps2)
        else:
            result[cmp_method] = similarity_count/min(num_kps1, num_kps2)
    return result

def get_similarity_scores(img1, img2, algorithm='SSIM'):
    assert(algorithm in CMP_ALGORITHMS)
    cmp_method = CMP_ALGORITHMS[algorithm]
    return cmp_method(img1, img2)

def run_img_comparisons(imgpath1, imgpath2, algorithms=list(CMP_ALGORITHMS.keys())):
    i1 = cv2.resize(cv2.imread(imgpath1, cv2.IMREAD_GRAYSCALE), SIM_IMAGE_SIZE)
    i2 = cv2.resize(cv2.imread(imgpath2, cv2.IMREAD_GRAYSCALE), SIM_IMAGE_SIZE)
    scores = {}
    for algo in algorithms:
        algo_scores = get_similarity_scores(i1, i2, algo)
        for score_name, score_value in algo_scores.items():
            LOGGER.debug(f'{score_name}: {score_value} for {os.path.basename(imgpath1)}<>{os.path.basename(imgpath2)}')
            scores[score_name] = score_value
    return scores

def main(arxiv_id, algos):  # arxiv_id including YYMM
    img_subdir = os.path.join(CONVERTED_IMG_FOLDER, arxiv_id)
    if not os.path.exists(img_subdir) or not os.path.isdir(img_subdir):
        LOGGER.debug(f'{img_subdir} not found - skipping')
        return {}
    images_in_dir = os.listdir(img_subdir)
    # split the images into comparison groups
    cmp_groups = {}
    for img_filename_with_ext in images_in_dir:
        img_filename = os.path.splitext(img_filename_with_ext)[0]
        _, engine, pg, pg_identifier = img_filename.split('_')
        if pg_identifier not in cmp_groups: cmp_groups[pg_identifier] = {}
        cmp_groups[pg_identifier][engine] = img_filename_with_ext
    # perform comparisons
    RESULT = {}
    assert('xe' in TEX_ENGINES)  # only for inter-engine
    CMP_BASELINE = 'xelatex'
    for pg, cmp_grp_members in cmp_groups.items():
        result_for_page = {}
        # comparisons within one group
        if len(cmp_grp_members) < 2 or CMP_BASELINE not in cmp_grp_members: continue
        baseline_img = os.path.join(img_subdir, cmp_grp_members.pop(CMP_BASELINE))
        for engine, img_filename in cmp_grp_members.items():
            img_filepath = os.path.join(img_subdir, img_filename)
            engine_result = run_img_comparisons(baseline_img, img_filepath, algos)
            for cmp_algo, value in engine_result.items():
                result_for_page[f'{CMP_BASELINE[:-5]}{engine[:-5]}_{cmp_algo}'] = value
        RESULT[pg] = result_for_page
    return RESULT

