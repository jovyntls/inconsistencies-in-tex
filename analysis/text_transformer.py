class TextTransformer:
    # pre-/post-transformations: applied before/after joining pages
    def __init__(self, pre_transformations, page_break_delimiter, post_transformations):
        self.page_break_delimiter = page_break_delimiter
        self.pre_transformations = pre_transformations
        self.post_transformations = post_transformations

    @staticmethod
    def apply_transform(text, transformations):
        for old, new in transformations:
            text = text.replace(old, new)
        return text

    def process(self, pages_arr):
        processed_pages = [TextTransformer.apply_transform(page, self.pre_transformations) for page in pages_arr]
        text = self.page_break_delimiter.join(processed_pages)
        return TextTransformer.apply_transform(text, self.post_transformations)

# common transforms ======================================================================
HYPHEN_BREAKS_TO_LINE_BREAK = ('-\n', '\n')  # check behaviour when used with line breaks
IGNORE_HYPHENS = ('-', '')
# for whitespace
LINE_BREAKS_TO_SPACES = ('\n', ' ')
IGNORE_SPACES = (' ', '')
# ligatures
COMMON_LIGATURES = [ ('ﬀ', 'ff'), ('ﬁ', 'fi'), ('ﬂ', 'fl'), ('ﬃ', 'ffi'), ('ﬄ', 'ffl') ]
# accents
COMMON_ACCENTS = [ ('¨o', 'ö'), ('¨a', 'ä'), ('¨u', 'ü'), ('˚a', 'å'), ('˚A', 'Å'), ('´a', 'á'), ('´A', 'Á'), 
                  ('´e', 'é'), ('´o', 'ó'), ('ˆe', 'ê'), ('´c', 'ć'), ('ˇs', 'š'), ('`e', 'è'), ('´O', 'Ó'), 
                  ('´s', 'ś'), ('¸c', 'ç'), ('˜a', 'ã'), ('¨O', 'Ö'), ('¨e', 'ë'), ('´E', 'É'), ('`a', 'à'),
                  ('˜A', 'Ã'), ('´ı', 'í'), ('ˆı', 'î'), ('˝o', 'ő'), ('`o', 'ò'), ('`u', 'ù'), ('`ı', 'ì'), 
                  ('`E', 'È'), ('ˇS', 'Š'), ('ˆz', 'ž'), ('ˇc', 'č'), ('´u', 'ú'), ('¯a', 'ā'), ('˘n', 'ń'),
                  ('ˇz', 'ž'), ('¨U', 'Ü'), ('ˇC', 'Č'), ('ˇR', 'Ř'), ('ˇr', 'ř'), ('ˇe', 'ě'), ('ˇa', 'ă'),
                  ('ˇZ', 'Ž'), ('ˆo', 'ô'), ('˘a', 'ă'), ('C¸', 'Ç'), ('¨ı', 'ï'), ('¯u', 'ū'), ('˜n', 'ñ'),
                  ('˙e', 'ė'), ('¸s', 'ş'), ('ˇn', 'ň'), ('ń', 'e'), ('¸S', 'Ş') ]

# common transformers ====================================================================
pretransformers = [ HYPHEN_BREAKS_TO_LINE_BREAK, LINE_BREAKS_TO_SPACES ]
posttransformers = COMMON_ACCENTS + COMMON_LIGATURES + [ IGNORE_SPACES ]
transformer_ignore_hyphenbreak_pagebreak_linebreak = TextTransformer(pretransformers, ' ', posttransformers)
