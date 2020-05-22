# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

import pytest
from pygments.lexers import get_lexer_by_name

from rhodecode.tests import no_newline_id_generator
from rhodecode.lib.codeblocks import (
    tokenize_string, split_token_stream, rollup_tokenstream,
    render_tokenstream)


class TestTokenizeString(object):

    python_code = '''
    import this

    var = 6
    print("this")

    '''

    def test_tokenize_as_python(self):
        lexer = get_lexer_by_name('python')
        tokens = list(tokenize_string(self.python_code, lexer))

        assert tokens == [
            ('',    u'\n'),
            ('',    u'    '),
            ('kn',  u'import'),
            ('',    u' '),
            ('nn',  u'this'),
            ('',    u'\n'),
            ('',    u'\n'),
            ('',    u'    '),
            ('n',   u'var'),
            ('',    u' '),
            ('o',   u'='),
            ('',    u' '),
            ('mi',  u'6'),
            ('',    u'\n'),
            ('',    u'    '),
            ('k',   u'print'),
            ('p', u'('),
            ('s2', u'"'),
            ('s2', u'this'),
            ('s2', u'"'),
            ('p', u')'),
            ('',    u'\n'),
            ('',    u'\n'),
            ('',    u'    ')
        ]

    def test_tokenize_as_text(self):
        lexer = get_lexer_by_name('text')
        tokens = list(tokenize_string(self.python_code, lexer))

        assert tokens == [
            ('',
            u'\n    import this\n\n    var = 6\n    print("this")\n\n    ')
        ]


class TestSplitTokenStream(object):

    def test_split_token_stream(self):
        tokens = [('type1', 'some\ntext'), ('type2', 'more\n')]
        content = [x + y for x, y in tokens]
        lines = list(split_token_stream(tokens, content))

        assert lines == [
            [('type1', u'some')],
            [('type1', u'text'), ('type2', u'more')],
            [('type2', u'')],
        ]

    def test_split_token_stream_single(self):
        tokens = [('type1', '\n')]
        content = [x + y for x, y in tokens]
        lines = list(split_token_stream(tokens, content))
        assert lines == [
            [('type1', '')],
            [('type1', '')],
        ]

    def test_split_token_stream_single_repeat(self):
        tokens = [('type1', '\n\n\n')]
        content = [x + y for x, y in tokens]
        lines = list(split_token_stream(tokens, content))
        assert lines == [
            [('type1', '')],
            [('type1', '')],
            [('type1', '')],
            [('type1', '')],
        ]

    def test_split_token_stream_multiple_repeat(self):
        tokens = [('type1', '\n\n'), ('type2', '\n\n')]
        content = [x + y for x, y in tokens]

        lines = list(split_token_stream(tokens, content))
        assert lines == [
            [('type1', '')],
            [('type1', '')],
            [('type1', ''), ('type2', '')],
            [('type2', '')],
            [('type2', '')],
        ]

    def test_no_tokens_by_content(self):
        tokens = []
        content = u'\ufeff'
        lines = list(split_token_stream(tokens, content))
        assert lines == [
            [('', content)],
        ]

    def test_no_tokens_by_valid_content(self):
        from pygments.lexers.css import CssLexer
        content = u'\ufeff table.dataTable'
        tokens = tokenize_string(content, CssLexer())

        lines = list(split_token_stream(tokens, content))
        assert lines == [
            [('', u' '),
             ('nt', u'table'),
             ('p', u'.'),
             ('nc', u'dataTable')],
        ]


class TestRollupTokens(object):

    @pytest.mark.parametrize('tokenstream,output', [
        ([],
            []),
        ([('A', 'hell'), ('A', 'o')], [
            ('A', [
                ('', 'hello')]),
        ]),
        ([('A', 'hell'), ('B', 'o')], [
            ('A', [
                ('', 'hell')]),
            ('B', [
                ('', 'o')]),
        ]),
        ([('A', 'hel'), ('A', 'lo'), ('B', ' '), ('A', 'there')], [
            ('A', [
                ('', 'hello')]),
            ('B', [
                ('', ' ')]),
            ('A', [
                ('', 'there')]),
        ]),
    ])
    def test_rollup_tokenstream_without_ops(self, tokenstream, output):
        assert list(rollup_tokenstream(tokenstream)) == output

    @pytest.mark.parametrize('tokenstream,output', [
        ([],
            []),
        ([('A', '', 'hell'), ('A', '', 'o')], [
            ('A', [
                ('', 'hello')]),
        ]),
        ([('A', '', 'hell'), ('B', '', 'o')], [
            ('A', [
                ('', 'hell')]),
            ('B', [
                ('', 'o')]),
        ]),
        ([('A', '', 'h'), ('B', '', 'e'), ('C', '', 'y')], [
            ('A', [
                ('', 'h')]),
            ('B', [
                ('', 'e')]),
            ('C', [
                ('', 'y')]),
        ]),
        ([('A', '', 'h'), ('A', '', 'e'), ('C', '', 'y')], [
            ('A', [
                ('', 'he')]),
            ('C', [
                ('', 'y')]),
        ]),
        ([('A', 'ins', 'h'), ('A', 'ins', 'e')], [
            ('A', [
                ('ins', 'he')
            ]),
        ]),
        ([('A', 'ins', 'h'), ('A', 'del', 'e')], [
            ('A', [
                ('ins', 'h'),
                ('del', 'e')
            ]),
        ]),
        ([('A', 'ins', 'h'), ('B', 'del', 'e'), ('B', 'del', 'y')], [
            ('A', [
                ('ins', 'h'),
            ]),
            ('B', [
                ('del', 'ey'),
            ]),
        ]),
        ([('A', 'ins', 'h'), ('A', 'del', 'e'), ('B', 'del', 'y')], [
            ('A', [
                ('ins', 'h'),
                ('del', 'e'),
            ]),
            ('B', [
                ('del', 'y'),
            ]),
        ]),
        ([('A', '', 'some'), ('A', 'ins', 'new'), ('A', '', 'name')], [
            ('A', [
                ('', 'some'),
                ('ins', 'new'),
                ('', 'name'),
            ]),
        ]),
    ])
    def test_rollup_tokenstream_with_ops(self, tokenstream, output):
        assert list(rollup_tokenstream(tokenstream)) == output


class TestRenderTokenStream(object):

    @pytest.mark.parametrize('tokenstream,output', [
        (
            [],
            '',
        ),
        (
            [('', '', u'')],
            '<span></span>',
        ),
        (
            [('', '', u'text')],
            '<span>text</span>',
        ),
        (
            [('A', '', u'')],
            '<span class="A"></span>',
        ),
        (
            [('A', '', u'hello')],
            '<span class="A">hello</span>',
        ),
        (
            [('A', '', u'hel'), ('A', '', u'lo')],
            '<span class="A">hello</span>',
        ),
        (
            [('A', '', u'two\n'), ('A', '', u'lines')],
            '<span class="A">two\nlines</span>',
        ),
        (
            [('A', '', u'\nthree\n'), ('A', '', u'lines')],
            '<span class="A">\nthree\nlines</span>',
        ),
        (
            [('', '', u'\n'), ('A', '', u'line')],
            '<span>\n</span><span class="A">line</span>',
        ),
        (
            [('', 'ins', u'\n'), ('A', '', u'line')],
            '<span><ins>\n</ins></span><span class="A">line</span>',
        ),
        (
            [('A', '', u'hel'), ('A', 'ins', u'lo')],
            '<span class="A">hel<ins>lo</ins></span>',
        ),
        (
            [('A', '', u'hel'), ('A', 'ins', u'l'), ('A', 'ins', u'o')],
            '<span class="A">hel<ins>lo</ins></span>',
        ),
        (
            [('A', '', u'hel'), ('A', 'ins', u'l'), ('A', 'del', u'o')],
            '<span class="A">hel<ins>l</ins><del>o</del></span>',
        ),
        (
            [('A', '', u'hel'), ('B', '', u'lo')],
            '<span class="A">hel</span><span class="B">lo</span>',
        ),
        (
            [('A', '', u'hel'), ('B', 'ins', u'lo')],
            '<span class="A">hel</span><span class="B"><ins>lo</ins></span>',
        ),
    ], ids=no_newline_id_generator)
    def test_render_tokenstream_with_ops(self, tokenstream, output):
        html = render_tokenstream(tokenstream)
        assert html == output

    @pytest.mark.parametrize('tokenstream,output', [
        (
            [('A', u'hel'), ('A', u'lo')],
            '<span class="A">hello</span>',
        ),
        (
            [('A', u'hel'), ('A', u'l'), ('A', u'o')],
            '<span class="A">hello</span>',
        ),
        (
            [('A', u'hel'), ('A', u'l'), ('A', u'o')],
            '<span class="A">hello</span>',
        ),
        (
            [('A', u'hel'), ('B', u'lo')],
            '<span class="A">hel</span><span class="B">lo</span>',
        ),
        (
            [('A', u'hel'), ('B', u'lo')],
            '<span class="A">hel</span><span class="B">lo</span>',
        ),
    ])
    def test_render_tokenstream_without_ops(self, tokenstream, output):
        html = render_tokenstream(tokenstream)
        assert html == output
