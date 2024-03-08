from typing import Any, Dict, Set

from text_based_comparison.extract import FontInformation
from utils.tex_engine_utils import DIFF_ENGINE_PAIRS

def run_font_comparison(pdf_fonts: Dict[str, Set[FontInformation]]):
    num_fonts: Dict[str, Any] = { 'comparison': 'fonts_num' }
    for e1, e2 in DIFF_ENGINE_PAIRS: 
        if e1 not in pdf_fonts or e2 not in pdf_fonts: continue
        col = f'{e1}{e2}'
        num_fonts[col] = abs(len(pdf_fonts[e1]) - len(pdf_fonts[e2]))
    return [num_fonts]


