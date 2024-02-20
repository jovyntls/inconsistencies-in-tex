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
COMMON_ACCENTS = [ ('C¸', 'Ç'), ('G¸', 'Ģ'), ('K¸', 'Ķ'), ('L¸', 'Ļ'), ('N¸', 'Ņ'), ('R¸', 'Ŗ'),
                  ('S¸', 'Ş'), ('T¸', 'Ţ'), ('`A', 'À'), ('`E', 'È'), ('`I', 'Ì'), ('`O', 'Ò'),
                  ('`U', 'Ù'), ('`a', 'à'), ('`e', 'è'), ('`o', 'ò'), ('`u', 'ù'), ('`ı', 'ì'),
                  ('c¸', 'ç'), ('g¸', 'ģ'), ('k¸', 'ķ'), ('l¸', 'ļ'), ('n¸', 'ņ'), ('r¸', 'ŗ'),
                  ('s¸', 'ş'), ('t¸', 'ţ'), ('¨A', 'Ä'), ('¨E', 'Ë'), ('¨I', 'Ï'), ('¨O', 'Ö'),
                  ('¨U', 'Ü'), ('¨Y', 'Ÿ'), ('¨a', 'ä'), ('¨e', 'ë'), ('¨i', 'ï'), ('¨o', 'ö'),
                  ('¨u', 'ü'), ('¨y', 'ÿ'), ('¨ı', 'ï'), ('¯A', 'Ā'), ('¯E', 'Ē'), ('¯G', 'Ḡ'),
                  ('¯I', 'Ī'), ('¯O', 'Ō'), ('¯U', 'Ū'), ('¯Y', 'Ȳ'), ('¯a', 'ā'), ('¯b', 'b̄'),
                  ('¯c', 'c̄'), ('¯u', 'ū'), ('´A', 'Á'), ('´C', 'Ć'), ('´E', 'É'), ('´I', 'Í'),
                  ('´L', 'Ĺ'), ('´N', 'Ń'), ('´O', 'Ó'), ('´R', 'Ŕ'), ('´S', 'Ś'), ('´U', 'Ú'),
                  ('´Y', 'Ý'), ('´Z', 'Ź'), ('´a', 'á'), ('´c', 'ć'), ('´e', 'é'), ('´l', 'ĺ'),
                  ('´n', 'ń'), ('´o', 'ó'), ('´r', 'ŕ'), ('´s', 'ś'), ('´u', 'ú'), ('´y', 'ý'),
                  ('´z', 'ź'), ('´ı', 'í'), ('¸S', 'Ş'), ('¸c', 'ç'), ('¸s', 'ş'), ('ˆA', 'Â'),
                  ('ˆC', 'Ĉ'), ('ˆE', 'Ê'), ('ˆG', 'Ĝ'), ('ˆH', 'Ĥ'), ('ˆI', 'Î'), ('ˆJ', 'Ĵ'),
                  ('ˆO', 'Ô'), ('ˆS', 'Ŝ'), ('ˆU', 'Û'), ('ˆa', 'â'), ('ˆc', 'ĉ'), ('ˆe', 'ê'),
                  ('ˆg', 'ĝ'), ('ˆh', 'ĥ'), ('ˆo', 'ô'), ('ˆs', 'ŝ'), ('ˆu', 'û'), ('ˆz', 'ž'),
                  ('ˆı', 'î'), ('ˆȷ', 'ĵ'), ('ˇA', 'Ǎ'), ('ˇC', 'Č'), ('ˇE', 'Ě'), ('ˇN', 'Ň'),
                  ('ˇR', 'Ř'), ('ˇS', 'Š'), ('ˇZ', 'Ž'), ('ˇa', 'ǎ'), ('ˇc', 'č'), ('ˇd', 'Ď'),
                  ('ˇe', 'ě'), ('ˇn', 'ň'), ('ˇr', 'ř'), ('ˇs', 'š'), ('ˇt', 'Ť'), ('ˇz', 'ž'),
                  ('˘A', 'Ă'), ('˘E', 'Ĕ'), ('˘G', 'Ğ'), ('˘I', 'Ĭ'), ('˘O', 'Ŏ'), ('˘U', 'Ŭ'),
                  ('˘a', 'ă'), ('˘e', 'ĕ'), ('˘g', 'ğ'), ('˘o', 'ŏ'), ('˘u', 'ŭ'), ('˘ı', 'ĭ'),
                  ('˙A', 'Ȧ'), ('˙B', 'Ḃ'), ('˙C', 'Ċ'), ('˙D', 'Ḋ'), ('˙E', 'Ė'), ('˙F', 'Ḟ'),
                  ('˙G', 'Ġ'), ('˙H', 'Ḣ'), ('˙I', 'İ'), ('˙L', 'Ŀ'), ('˙N', 'Ṅ'), ('˙O', 'Ȯ'),
                  ('˙P', 'Ṗ'), ('˙R', 'Ṙ'), ('˙S', 'Ṡ'), ('˙T', 'Ṫ'), ('˙X', 'Ẋ'), ('˙Y', 'Ẏ'),
                  ('˙Z', 'Ż'), ('˙a', 'ȧ'), ('˙b', 'ḃ'), ('˙c', 'ċ'), ('˙d', 'ḋ'), ('˙e', 'ė'),
                  ('˙f', 'ḟ'), ('˙g', 'ġ'), ('˙h', 'ḣ'), ('˙l', 'ŀ'), ('˙n', 'ṅ'), ('˙o', 'ȯ'),
                  ('˙p', 'ṗ'), ('˙r', 'ṙ'), ('˙s', 'ṡ'), ('˙t', 'ṫ'), ('˙x', 'ẋ'), ('˙y', 'ẏ'),
                  ('˙z', 'ż'), ('˙ı', 'i'), ('˚A', 'Å'), ('˚U', 'Ů'), ('˚a', 'å'), ('˚u', 'ů'),
                  ('˚w', 'ẘ'), ('˚y', 'ẙ'), ('˜A', 'Ã'), ('˜I', 'Ĩ'), ('˜N', 'Ñ'), ('˜O', 'Õ'),
                  ('˜U', 'Ũ'), ('˜a', 'ã'), ('˜n', 'ñ'), ('˜o', 'õ'), ('˜u', 'ũ'), ('˜ı', 'ĩ'),
                  ('˝O', 'Ő'), ('˝U', 'Ű'), ('˝o', 'ő'), ('˝u', 'ű') ]

# common transformers ====================================================================
pretransformers = [ HYPHEN_BREAKS_TO_LINE_BREAK, LINE_BREAKS_TO_SPACES ]
posttransformers = COMMON_ACCENTS + COMMON_LIGATURES + [ IGNORE_SPACES ]
transformer_ignore_hyphenbreak_pagebreak_linebreak = TextTransformer(pretransformers, ' ', posttransformers)
