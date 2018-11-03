# =============================================================================
#  END OF UTILITY FUNCTIONS HERE
# =============================================================================

# Additional mappings that are not present in the pygments lexers
# used for building stats
# format is {'ext':['Names']} eg. {'py':['Python']} note: there can be
# more than one name for extension
# NOTE: that this will override any mappings in LANGUAGES_EXTENSIONS_MAP
# build by pygments
EXTRA_MAPPINGS = {'html': ['Text']}

# additional lexer definitions for custom files it's overrides pygments lexers,
# and uses defined name of lexer to colorize the files. Format is {'ext':
# 'lexer_name'} List of lexers can be printed running:
#   >> python -c "import pprint;from pygments import lexers;
#           pprint.pprint([(x[0], x[1]) for x in lexers.get_all_lexers()]);"

EXTRA_LEXERS = {
    'tt': 'vbnet'
}
