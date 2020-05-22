# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

import copy
import mock
import pytest

from rhodecode.lib.index import search_utils


@pytest.mark.parametrize('test_text, expected_output', [
    ('some text', ['some', 'text']),
    ('some    text', ['some', 'text']),
    ('some text "with  a phrase"', ['some', 'text', 'with  a phrase']),
    ('"a phrase" "another phrase"', ['a phrase', 'another phrase']),
    ('"justphrase"', ['justphrase']),
    ('""', []),
    ('', []),
    ('  ', []),
    ('"   "', []),
])
def test_extract_phrases(test_text, expected_output):
    assert search_utils.extract_phrases(test_text) == expected_output


@pytest.mark.parametrize('test_text, text_phrases, expected_output', [
    ('some text here', ['some', 'here'], [(0, 4), (10, 14)]),
    ('here here there', ['here'], [(0, 4), (5, 9), (11, 15)]),
    ('irrelevant', ['not found'], []),
    ('irrelevant', ['not found'], []),
])
def test_get_matching_phrase_offsets(test_text, text_phrases, expected_output):
    assert search_utils.get_matching_phrase_offsets(
        test_text, text_phrases) == expected_output


@pytest.mark.parametrize('test_text, text_phrases, expected_output', [
    ('__RCSearchHLMarkBEG__some__RCSearchHLMarkEND__ text __RCSearchHLMarkBEG__here__RCSearchHLMarkEND__', [], [(0, 46), (52, 98)]),
    ('__RCSearchHLMarkBEG__here__RCSearchHLMarkEND__ __RCSearchHLMarkBEG__here__RCSearchHLMarkEND__ there', [], [(0, 46), (47, 93)]),
    ('some text __RCSearchHLMarkBEG__here__RCSearchHLMarkEND__', [], [(10, 56)]),
    ('__RCSearchHLMarkBEG__here__RCSearchHLMarkEND__ __RCSearchHLMarkBEG__here__RCSearchHLMarkEND__ __RCSearchHLMarkBEG__there__RCSearchHLMarkEND__', [], [(0, 46), (47, 93), (94, 141)]),
    ('irrelevant', ['not found'], []),
    ('irrelevant', ['not found'], []),
])
def test_get_matching_marker_offsets(test_text, text_phrases, expected_output):

    assert search_utils.get_matching_markers_offsets(test_text) == expected_output


def test_normalize_text_for_matching():
    assert search_utils.normalize_text_for_matching(
        'OJjfe)*#$*@)$JF*)3r2f80h') == 'ojjfe        jf  3r2f80h'


def test_get_matching_line_offsets():
    words = '\n'.join([
        'words words words',
        'words words words',
        'some text some',
        'words words words',
        'words words words',
        'text here what'
    ])
    total_lines, matched_offsets = \
        search_utils.get_matching_line_offsets(words, terms='text')
    assert total_lines == 6
    assert matched_offsets == {3: [(5, 9)], 6: [(0, 4)]}


def test_get_matching_line_offsets_using_markers():
    words = '\n'.join([
        'words words words',
        'words words words',
        'some __1__text__2__ some',
        'words words words',
        'words words words',
        '__1__text__2__ here what'
    ])
    total_lines, matched_offsets = \
        search_utils.get_matching_line_offsets(words, terms=None,
                                               markers=['__1__(.*?)__2__'])
    assert total_lines == 6
    assert matched_offsets == {3: [(5, 19)], 6: [(0, 14)]}
