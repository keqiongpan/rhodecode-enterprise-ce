# -*- coding: utf-8 -*-

# Copyright (C) 2011-2016  RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/


from itertools import groupby

from pygments import lex
# PYGMENTS_TOKEN_TYPES is used in a hot loop keep attribute lookups to a minimum
from pygments.token import STANDARD_TYPES as PYGMENTS_TOKEN_TYPES

from rhodecode.lib.helpers import get_lexer_for_filenode

def tokenize_file(content, lexer):
    """
    Use pygments to tokenize some content based on a lexer
    ensuring all original new lines and whitespace is preserved
    """

    lexer.stripall = False
    lexer.stripnl = False
    lexer.ensurenl = False
    return lex(content, lexer)


def pygment_token_class(token_type):
    """ Convert a pygments token type to html class name """

    fname = PYGMENTS_TOKEN_TYPES.get(token_type)
    if fname:
        return fname

    aname = ''
    while fname is None:
        aname = '-' + token_type[-1] + aname
        token_type = token_type.parent
        fname = PYGMENTS_TOKEN_TYPES.get(token_type)

    return fname + aname


def tokens_as_lines(tokens, split_string=u'\n'):
    """
    Take a list of (TokenType, text) tuples and split them by a string

    eg. [(TEXT, 'some\ntext')] => [(TEXT, 'some'), (TEXT, 'text')]
    """

    buffer = []
    for token_type, token_text in tokens:
        parts = token_text.split(split_string)
        for part in parts[:-1]:
            buffer.append((token_type, part))
            yield buffer
            buffer = []

        buffer.append((token_type, parts[-1]))

    if buffer:
        yield buffer


def filenode_as_lines_tokens(filenode):
    """
    Return a generator of lines with pygment tokens for a filenode eg:

    [
        (1, line1_tokens_list),
        (2, line1_tokens_list]),
    ]
    """

    return enumerate(
      tokens_as_lines(
        tokenize_file(
          filenode.content, get_lexer_for_filenode(filenode)
        )
      ),
    1)


def filenode_as_annotated_lines_tokens(filenode):
    """
    Take a file node and return a list of annotations => lines, if no annotation
    is found, it will be None.

    eg:

    [
        (annotation1, [
            (1, line1_tokens_list),
            (2, line2_tokens_list),
        ]),
        (annotation2, [
            (3, line1_tokens_list),
        ]),
        (None, [
            (4, line1_tokens_list),
        ]),
        (annotation1, [
            (5, line1_tokens_list),
            (6, line2_tokens_list),
        ])
    ]
    """


    # cache commit_getter lookups
    commit_cache = {}
    def _get_annotation(commit_id, commit_getter):
        if commit_id not in commit_cache:
            commit_cache[commit_id] = commit_getter()
        return commit_cache[commit_id]

    annotation_lookup = {
        line_no: _get_annotation(commit_id, commit_getter)
        for line_no, commit_id, commit_getter, line_content
        in filenode.annotate
    }

    annotations_lines = ((annotation_lookup.get(line_no), line_no, tokens)
                          for line_no, tokens
                          in filenode_as_lines_tokens(filenode))

    grouped_annotations_lines = groupby(annotations_lines, lambda x: x[0])

    for annotation, group in grouped_annotations_lines:
        yield (
            annotation, [(line_no, tokens)
                          for (_, line_no, tokens) in group]
        )
