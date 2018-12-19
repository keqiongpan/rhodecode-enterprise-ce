# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 RhodeCode GmbH
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
import re

import pygments.filter
import pygments.filters
from pygments.token import Comment

HL_BEG_MARKER = '__RCSearchHLMarkBEG__'
HL_END_MARKER = '__RCSearchHLMarkEND__'
HL_MARKER_RE = '{}(.*?){}'.format(HL_BEG_MARKER, HL_END_MARKER)


class ElasticSearchHLFilter(pygments.filters.Filter):
    _names = [HL_BEG_MARKER, HL_END_MARKER]

    def __init__(self, **options):
        pygments.filters.Filter.__init__(self, **options)

    def filter(self, lexer, stream):
        def tokenize(_value):
            for token in re.split('({}|{})'.format(
                    self._names[0], self._names[1]), _value):
                if token:
                    yield token

        hl = False
        for ttype, value in stream:

            if self._names[0] in value or self._names[1] in value:
                for item in tokenize(value):
                    if item == self._names[0]:
                        # skip marker, but start HL
                        hl = True
                        continue
                    elif item == self._names[1]:
                        hl = False
                        continue

                    if hl:
                        yield Comment.ElasticMatch, item
                    else:
                        yield ttype, item
            else:
                if hl:
                    yield Comment.ElasticMatch, value
                else:
                    yield ttype, value


def extract_phrases(text_query):
    """
    Extracts phrases from search term string making sure phrases
    contained in double quotes are kept together - and discarding empty values
    or fully whitespace values eg.

    'some   text "a phrase" more' => ['some', 'text', 'a phrase', 'more']

    """

    in_phrase = False
    buf = ''
    phrases = []
    for char in text_query:
        if in_phrase:
            if char == '"':  # end phrase
                phrases.append(buf)
                buf = ''
                in_phrase = False
                continue
            else:
                buf += char
                continue
        else:
            if char == '"':  # start phrase
                in_phrase = True
                phrases.append(buf)
                buf = ''
                continue
            elif char == ' ':
                phrases.append(buf)
                buf = ''
                continue
            else:
                buf += char

    phrases.append(buf)
    phrases = [phrase.strip() for phrase in phrases if phrase.strip()]
    return phrases


def get_matching_phrase_offsets(text, phrases):
    """
    Returns a list of string offsets in `text` that the list of `terms` match

    >>> get_matching_phrase_offsets('some text here', ['some', 'here'])
    [(0, 4), (10, 14)]

    """
    phrases = phrases or []
    offsets = []

    for phrase in phrases:
        for match in re.finditer(phrase, text):
            offsets.append((match.start(), match.end()))

    return offsets


def get_matching_markers_offsets(text, markers=None):
    """
    Returns a list of string offsets in `text` that the are between matching markers

    >>> get_matching_markers_offsets('$1some$2 text $1here$2 marked', ['\$1(.*?)\$2'])
    [(0, 5), (16, 22)]

    """
    markers = markers or [HL_MARKER_RE]
    offsets = []

    if markers:
        for mark in markers:
            for match in re.finditer(mark, text):
                offsets.append((match.start(), match.end()))

    return offsets


def normalize_text_for_matching(x):
    """
    Replaces all non alfanum characters to spaces and lower cases the string,
    useful for comparing two text strings without punctuation
    """
    return re.sub(r'[^\w]', ' ', x.lower())


def get_matching_line_offsets(lines, terms=None, markers=None):
    """ Return a set of `lines` indices (starting from 1) matching a
    text search query, along with `context` lines above/below matching lines

    :param lines: list of strings representing lines
    :param terms: search term string to match in lines eg. 'some text'
    :param markers: instead of terms, use highlight markers instead that
        mark beginning and end for matched item. eg. ['START(.*?)END']

     eg.

    text = '''
    words words words
    words words words
    some text some
    words words words
    words words words
    text here what
    '''
    get_matching_line_offsets(text, 'text', context=1)
    6, {3: [(5, 9)], 6: [(0, 4)]]

    """
    matching_lines = {}
    line_index = 0

    if terms:
        phrases = [normalize_text_for_matching(phrase)
                   for phrase in extract_phrases(terms)]

        for line_index, line in enumerate(lines.splitlines(), start=1):
            normalized_line = normalize_text_for_matching(line)
            match_offsets = get_matching_phrase_offsets(normalized_line, phrases)
            if match_offsets:
                matching_lines[line_index] = match_offsets

    else:
        markers = markers or [HL_MARKER_RE]
        for line_index, line in enumerate(lines.splitlines(), start=1):
            match_offsets = get_matching_markers_offsets(line, markers=markers)
            if match_offsets:
                matching_lines[line_index] = match_offsets

    return line_index, matching_lines


def lucene_query_parser():
    # from pyparsing lucene_grammar
    from pyparsing import (
        Literal, CaselessKeyword, Forward, Regex, QuotedString, Suppress,
        Optional, Group, infixNotation, opAssoc, ParserElement, pyparsing_common)

    ParserElement.enablePackrat()

    COLON, LBRACK, RBRACK, LBRACE, RBRACE, TILDE, CARAT = map(Literal, ":[]{}~^")
    LPAR, RPAR = map(Suppress, "()")
    and_, or_, not_, to_ = map(CaselessKeyword, "AND OR NOT TO".split())
    keyword = and_ | or_ | not_ | to_

    expression = Forward()

    valid_word = Regex(r'([a-zA-Z0-9*_+.-]|\\[!(){}\[\]^"~*?\\:])+').setName("word")
    valid_word.setParseAction(
        lambda t: t[0]
            .replace('\\\\', chr(127))
            .replace('\\', '')
            .replace(chr(127), '\\')
    )

    string = QuotedString('"')

    required_modifier = Literal("+")("required")
    prohibit_modifier = Literal("-")("prohibit")
    integer = Regex(r"\d+").setParseAction(lambda t: int(t[0]))
    proximity_modifier = Group(TILDE + integer("proximity"))
    number = pyparsing_common.fnumber()
    fuzzy_modifier = TILDE + Optional(number, default=0.5)("fuzzy")

    term = Forward()
    field_name = valid_word().setName("fieldname")
    incl_range_search = Group(LBRACK + term("lower") + to_ + term("upper") + RBRACK)
    excl_range_search = Group(LBRACE + term("lower") + to_ + term("upper") + RBRACE)
    range_search = incl_range_search("incl_range") | excl_range_search("excl_range")
    boost = (CARAT + number("boost"))

    string_expr = Group(string + proximity_modifier) | string
    word_expr = Group(valid_word + fuzzy_modifier) | valid_word
    term << (Optional(field_name("field") + COLON) +
             (word_expr | string_expr | range_search | Group(
                 LPAR + expression + RPAR)) +
             Optional(boost))
    term.setParseAction(lambda t: [t] if 'field' in t or 'boost' in t else None)

    expression << infixNotation(
        term,
        [
            (required_modifier | prohibit_modifier, 1, opAssoc.RIGHT),
            ((not_ | '!').setParseAction(lambda: "NOT"), 1, opAssoc.RIGHT),
            ((and_ | '&&').setParseAction(lambda: "AND"), 2, opAssoc.LEFT),
            (Optional(or_ | '||').setParseAction(lambda: "OR"), 2, opAssoc.LEFT),
        ]
    )

    return expression
