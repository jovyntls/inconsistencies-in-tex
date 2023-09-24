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
# for whitespace
LINE_BREAKS_TO_SPACES = ('\n', ' ')
IGNORE_SPACES = (' ', '')
# ligatures
COMMON_LIGATURES = [ ('ﬀ', 'ff'), ('ﬁ', 'fi'), ('ﬂ', 'fl'), ('ﬃ', 'ffi') ]
# accents
COMMON_ACCENTS = [ ('¨o', 'ö'), ('¨a', 'ä'), ('¨u', 'ü'), ('˚a', 'å'), ('˚A', 'Å') ]

# common transformers ====================================================================
pretransformers = [ HYPHEN_BREAKS_TO_LINE_BREAK, LINE_BREAKS_TO_SPACES ]
posttransformers = COMMON_ACCENTS + COMMON_LIGATURES + [ IGNORE_SPACES ]
transformer_ignore_hyphenbreak_pagebreak_linebreak = TextTransformer(pretransformers, ' ', posttransformers)
