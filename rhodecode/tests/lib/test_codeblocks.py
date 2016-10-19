# -*- coding: utf-8 -*-

# Copyright (C) 2016-2016  RhodeCode GmbH
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

from rhodecode.lib.codeblocks import (
    tokenize_string, split_token_stream, rollup_tokenstream,
    render_tokenstream)
from pygments.lexers import get_lexer_by_name


class TestTokenizeString(object):

    python_code = '''
    import this

    var = 6
    print "this"

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
            ('',    u' '),
            ('s2',  u'"'),
            ('s2',  u'this'),
            ('s2',  u'"'),
            ('',    u'\n'),
            ('',    u'\n'),
            ('',    u'    ')
        ]

    def test_tokenize_as_text(self):
        lexer = get_lexer_by_name('text')
        tokens = list(tokenize_string(self.python_code, lexer))

        assert tokens == [
            ('',
            u'\n    import this\n\n    var = 6\n    print "this"\n\n    ')
        ]


class TestSplitTokenStream(object):

    def test_split_token_stream(self):
        lines = list(split_token_stream(
            [('type1', 'some\ntext'), ('type2', 'more\n')]))

        assert lines == [
            [('type1', u'some')],
            [('type1', u'text'), ('type2', u'more')],
            [('type2', u'')],
        ]

    def test_split_token_stream_other_char(self):
        lines = list(split_token_stream(
            [('type1', 'some\ntext'), ('type2', 'more\n')],
            split_string='m'))

        assert lines == [
            [('type1', 'so')],
            [('type1', 'e\ntext'), ('type2', '')],
            [('type2', 'ore\n')],
        ]

    def test_split_token_stream_without_char(self):
        lines = list(split_token_stream(
            [('type1', 'some\ntext'), ('type2', 'more\n')],
            split_string='z'))

        assert lines == [
            [('type1', 'some\ntext'), ('type2', 'more\n')]
        ]

    def test_split_token_stream_single(self):
        lines = list(split_token_stream(
            [('type1', '\n')], split_string='\n'))

        assert lines == [
            [('type1', '')],
            [('type1', '')],
        ]

    def test_split_token_stream_single_repeat(self):
        lines = list(split_token_stream(
            [('type1', '\n\n\n')], split_string='\n'))

        assert lines == [
            [('type1', '')],
            [('type1', '')],
            [('type1', '')],
            [('type1', '')],
        ]

    def test_split_token_stream_multiple_repeat(self):
        lines = list(split_token_stream(
            [('type1', '\n\n'), ('type2', '\n\n')], split_string='\n'))

        assert lines == [
            [('type1', '')],
            [('type1', '')],
            [('type1', ''), ('type2', '')],
            [('type2', '')],
            [('type2', '')],
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
            '<span class="A">two<nl>\n</nl>lines</span>',
        ),
        (
            [('A', '', u'\nthree\n'), ('A', '', u'lines')],
            '<span class="A"><nl>\n</nl>three<nl>\n</nl>lines</span>',
        ),
        (
            [('', '', u'\n'), ('A', '', u'line')],
            '<span><nl>\n</nl></span><span class="A">line</span>',
        ),
        (
            [('', 'ins', u'\n'), ('A', '', u'line')],
            '<span><ins><nl>\n</nl></ins></span><span class="A">line</span>',
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
    ])
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
