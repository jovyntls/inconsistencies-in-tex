from typing import Any, Dict, Set

from analysis.helpers import COMPARISON
from text_based_comparison.extract import FontInformation

def run_font_comparison(pdf_fonts: Dict[str, Set[FontInformation]]):
    num_fonts: Dict[str, Any] = { 'comparison': 'fonts_num' }
    for e1, e2 in COMPARISON: 
        if e1 not in pdf_fonts or e2 not in pdf_fonts: continue
        col = f'{e1}{e2}'
        num_fonts[col] = abs(len(pdf_fonts[e1]) - len(pdf_fonts[e2]))
    return [num_fonts]


