from typing import Any, Dict, Set

from text_based_comparison.extract import FontInformation
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS
from utils.logger import ANALYSIS_LOGGER as LOGGER

def run_font_comparison(pdf_fonts: Dict[str, Set[FontInformation]]):
    num_fonts: Dict[str, Any] = { 'comparison': 'fonts_num' }
    uniq_fonts: Dict[str, Any] = { 'comparison': 'fonts_uniq' }
    for e1, e2 in DIFF_ENGINE_PAIRS: 
        if e1 not in pdf_fonts or e2 not in pdf_fonts: continue
        col = f'{e1}{e2}'
        e1_fonts, e2_fonts = pdf_fonts[e1], pdf_fonts[e2]
        num_fonts[col] = abs(len(e1_fonts) - len(e2_fonts))
        num_diff_fonts = len((e1_fonts - e2_fonts) | (e2_fonts - e1_fonts))
        if num_diff_fonts > 0:
            difffonts1 = "\n\t".join([str(s) for s in e1_fonts-e2_fonts])
            difffonts2 = "\n\t".join([str(s) for s in e2_fonts-e1_fonts])
            LOGGER.debug(f'found {num_diff_fonts} different fonts:\n{e1}:\n\t{difffonts1}\n{e2}:\n\t{difffonts2}')
        uniq_fonts[col] = num_diff_fonts
    return [num_fonts, uniq_fonts]


