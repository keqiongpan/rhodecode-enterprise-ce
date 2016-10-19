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

import logging
from itertools import groupby

from pygments import lex
from pygments.formatters.html import _get_ttype_class as pygment_token_class
from rhodecode.lib.helpers import get_lexer_for_filenode, html_escape
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.lib.vcs.nodes import FileNode
from pygments.lexers import get_lexer_by_name

plain_text_lexer = get_lexer_by_name(
    'text', stripall=False, stripnl=False, ensurenl=False)


log = logging.getLogger()


def filenode_as_lines_tokens(filenode, lexer=None):
    lexer = lexer or get_lexer_for_filenode(filenode)
    log.debug('Generating file node pygment tokens for %s, %s', lexer, filenode)
    tokens = tokenize_string(filenode.content, get_lexer_for_filenode(filenode))
    lines = split_token_stream(tokens, split_string='\n')
    rv = list(lines)
    return rv


def tokenize_string(content, lexer):
    """
    Use pygments to tokenize some content based on a lexer
    ensuring all original new lines and whitespace is preserved
    """

    lexer.stripall = False
    lexer.stripnl = False
    lexer.ensurenl = False
    for token_type, token_text in lex(content, lexer):
        yield pygment_token_class(token_type), token_text


def split_token_stream(tokens, split_string=u'\n'):
    """
    Take a list of (TokenType, text) tuples and split them by a string

    >>> split_token_stream([(TEXT, 'some\ntext'), (TEXT, 'more\n')])
    [(TEXT, 'some'), (TEXT, 'text'),
     (TEXT, 'more'), (TEXT, 'text')]
    """

    buffer = []
    for token_class, token_text in tokens:
        parts = token_text.split(split_string)
        for part in parts[:-1]:
            buffer.append((token_class, part))
            yield buffer
            buffer = []

        buffer.append((token_class, parts[-1]))

    if buffer:
        yield buffer


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

    commit_cache = {} # cache commit_getter lookups

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
                          in enumerate(filenode_as_lines_tokens(filenode), 1))

    grouped_annotations_lines = groupby(annotations_lines, lambda x: x[0])

    for annotation, group in grouped_annotations_lines:
        yield (
            annotation, [(line_no, tokens)
                          for (_, line_no, tokens) in group]
        )


def render_tokenstream(tokenstream):
    result = []
    for token_class, token_ops_texts in rollup_tokenstream(tokenstream):

        if token_class:
            result.append(u'<span class="%s">' % token_class)
        else:
            result.append(u'<span>')

        for op_tag, token_text in token_ops_texts:

            if op_tag:
                result.append(u'<%s>' % op_tag)

            escaped_text = html_escape(token_text)
            escaped_text = escaped_text.replace('\n', '<nl>\n</nl>')

            result.append(escaped_text)

            if op_tag:
                result.append(u'</%s>' % op_tag)

        result.append(u'</span>')

    html = ''.join(result)
    return html


def rollup_tokenstream(tokenstream):
    """
    Group a token stream of the format:

        ('class', 'op', 'text')
    or
        ('class', 'text')

    into

        [('class1',
            [('op1', 'text'),
             ('op2', 'text')]),
         ('class2',
            [('op3', 'text')])]

    This is used to get the minimal tags necessary when
    rendering to html eg for a token stream ie.

    <span class="A"><ins>he</ins>llo</span>
    vs
    <span class="A"><ins>he</ins></span><span class="A">llo</span>

    If a 2 tuple is passed in, the output op will be an empty string.

    eg:

    >>> rollup_tokenstream([('classA', '',      'h'),
                            ('classA', 'del',   'ell'),
                            ('classA', '',      'o'),
                            ('classB', '',      ' '),
                            ('classA', '',      'the'),
                            ('classA', '',      're'),
                            ])

    [('classA', [('', 'h'), ('del', 'ell'), ('', 'o')],
     ('classB', [('', ' ')],
     ('classA', [('', 'there')]]

    """
    if tokenstream and len(tokenstream[0]) == 2:
        tokenstream = ((t[0], '', t[1]) for t in tokenstream)

    result = []
    for token_class, op_list in groupby(tokenstream, lambda t: t[0]):
        ops = []
        for token_op, token_text_list in groupby(op_list, lambda o: o[1]):
            text_buffer = []
            for t_class, t_op, t_text in token_text_list:
                text_buffer.append(t_text)
            ops.append((token_op, ''.join(text_buffer)))
        result.append((token_class, ops))
    return result
