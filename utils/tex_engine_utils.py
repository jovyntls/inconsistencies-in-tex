TEX_ENGINES = ['pdflatex', 'lualatex', 'xelatex']

DIFF_ENGINE_PAIRS = [(TEX_ENGINES[-1], engine) for engine in TEX_ENGINES[:-1]]

def get_compile_tex_commands(arxiv_id, output_folder):
    COMPILE_TEX_COMMANDS = {
        'pdflatex': [
            'latexmk',
            '-pdf',
            '-output-format=pdf',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_pdflatex',
            f'-output-directory={output_folder}'
        ], 
        'lualatex': [
            'lualatex',
            '-lualatex',
            '-output-format=pdf',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_lualatex',
            f'-output-directory={output_folder}'
        ],
        'xelatex': [
            'xelatex',
            '-xelatex',
            '-output-format=pdf',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_xelatex',
            f'-output-directory={output_folder}'
        ]
    }
    assert(set(TEX_ENGINES) == set(COMPILE_TEX_COMMANDS.keys()))
    return COMPILE_TEX_COMMANDS
