TEX_ENGINES = ['pdf', 'lua', 'xe']
DIFF_ENGINE_PAIRS = [ ('xe', 'pdf'), ('xe', 'lua') ]
TEX_ENGINES_NAMES = { 'pdf': 'pdflatex', 'lua': 'lualatex', 'xe': 'xelatex'}

# TEX_ENGINES = ['20', '21', '22', '23']
# DIFF_ENGINE_PAIRS = [('20', '21'), ('21', '22'), ('22', '23'), ('20', '23')]
# TEX_ENGINES_NAMES = {'20': 'tl2020', '21': 'tl2021', '22': 'tl2022', '23': 'tl2023'}

def get_engine_name(engine):
    return TEX_ENGINES_NAMES[engine]

def get_compile_tex_commands(arxiv_id, output_folder):
    COMPILE_TEX_COMMANDS = {
        'pdf': [
            'latexmk',
            '-pdf',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_pdflatex',
            f'-output-directory={output_folder}'
        ], 
        'lua': [
            'latexmk',
            '-lualatex',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_lualatex',
            f'-output-directory={output_folder}'
        ],
        'xe': [
            'latexmk',
            '-xelatex',
            '-interaction=nonstopmode',
            f'-jobname={arxiv_id}_xelatex',
            f'-output-directory={output_folder}'
        ]
    }
    assert(set(TEX_ENGINES) == set(COMPILE_TEX_COMMANDS.keys()))
    return COMPILE_TEX_COMMANDS
