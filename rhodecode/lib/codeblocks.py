# -*- coding: utf-8 -*-

# Copyright (C) 2011-2017 RhodeCode GmbH
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
import difflib
from itertools import groupby

from pygments import lex
from pygments.formatters.html import _get_ttype_class as pygment_token_class
from rhodecode.lib.helpers import (
    get_lexer_for_filenode, html_escape, get_custom_lexer)
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.lib.diff_match_patch import diff_match_patch
from rhodecode.lib.diffs import LimitedDiffContainer
from pygments.lexers import get_lexer_by_name

plain_text_lexer = get_lexer_by_name(
    'text', stripall=False, stripnl=False, ensurenl=False)


log = logging.getLogger()


def filenode_as_lines_tokens(filenode, lexer=None):
    org_lexer = lexer
    lexer = lexer or get_lexer_for_filenode(filenode)
    log.debug('Generating file node pygment tokens for %s, %s, org_lexer:%s',
              lexer, filenode, org_lexer)
    tokens = tokenize_string(filenode.content, lexer)
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

    commit_cache = {}  # cache commit_getter lookups

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

            # TODO: dan: investigate showing hidden characters like space/nl/tab
            # escaped_text = escaped_text.replace(' ', '<sp> </sp>')
            # escaped_text = escaped_text.replace('\n', '<nl>\n</nl>')
            # escaped_text = escaped_text.replace('\t', '<tab>\t</tab>')

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


def tokens_diff(old_tokens, new_tokens, use_diff_match_patch=True):
    """
    Converts a list of (token_class, token_text) tuples to a list of
    (token_class, token_op, token_text) tuples where token_op is one of
    ('ins', 'del', '')

    :param old_tokens: list of (token_class, token_text) tuples of old line
    :param new_tokens: list of (token_class, token_text) tuples of new line
    :param use_diff_match_patch: boolean, will use google's diff match patch
        library which has options to 'smooth' out the character by character
        differences making nicer ins/del blocks
    """

    old_tokens_result = []
    new_tokens_result = []

    similarity = difflib.SequenceMatcher(None,
        ''.join(token_text for token_class, token_text in old_tokens),
        ''.join(token_text for token_class, token_text in new_tokens)
    ).ratio()

    if similarity < 0.6: # return, the blocks are too different
        for token_class, token_text in old_tokens:
            old_tokens_result.append((token_class, '', token_text))
        for token_class, token_text in new_tokens:
            new_tokens_result.append((token_class, '', token_text))
        return old_tokens_result, new_tokens_result, similarity

    token_sequence_matcher = difflib.SequenceMatcher(None,
        [x[1] for x in old_tokens],
        [x[1] for x in new_tokens])

    for tag, o1, o2, n1, n2 in token_sequence_matcher.get_opcodes():
        # check the differences by token block types first to give a more
        # nicer "block" level replacement vs character diffs

        if tag == 'equal':
            for token_class, token_text in old_tokens[o1:o2]:
                old_tokens_result.append((token_class, '', token_text))
            for token_class, token_text in new_tokens[n1:n2]:
                new_tokens_result.append((token_class, '', token_text))
        elif tag == 'delete':
            for token_class, token_text in old_tokens[o1:o2]:
                old_tokens_result.append((token_class, 'del', token_text))
        elif tag == 'insert':
            for token_class, token_text in new_tokens[n1:n2]:
                new_tokens_result.append((token_class, 'ins', token_text))
        elif tag == 'replace':
            # if same type token blocks must be replaced, do a diff on the
            # characters in the token blocks to show individual changes

            old_char_tokens = []
            new_char_tokens = []
            for token_class, token_text in old_tokens[o1:o2]:
                for char in token_text:
                    old_char_tokens.append((token_class, char))

            for token_class, token_text in new_tokens[n1:n2]:
                for char in token_text:
                    new_char_tokens.append((token_class, char))

            old_string = ''.join([token_text for
                token_class, token_text in old_char_tokens])
            new_string = ''.join([token_text for
                token_class, token_text in new_char_tokens])

            char_sequence = difflib.SequenceMatcher(
                None, old_string, new_string)
            copcodes = char_sequence.get_opcodes()
            obuffer, nbuffer = [], []

            if use_diff_match_patch:
                dmp = diff_match_patch()
                dmp.Diff_EditCost = 11 # TODO: dan: extract this to a setting
                reps = dmp.diff_main(old_string, new_string)
                dmp.diff_cleanupEfficiency(reps)

                a, b = 0, 0
                for op, rep in reps:
                    l = len(rep)
                    if op == 0:
                        for i, c in enumerate(rep):
                            obuffer.append((old_char_tokens[a+i][0], '', c))
                            nbuffer.append((new_char_tokens[b+i][0], '', c))
                        a += l
                        b += l
                    elif op == -1:
                        for i, c in enumerate(rep):
                            obuffer.append((old_char_tokens[a+i][0], 'del', c))
                        a += l
                    elif op == 1:
                        for i, c in enumerate(rep):
                            nbuffer.append((new_char_tokens[b+i][0], 'ins', c))
                        b += l
            else:
                for ctag, co1, co2, cn1, cn2 in copcodes:
                    if ctag == 'equal':
                        for token_class, token_text in old_char_tokens[co1:co2]:
                            obuffer.append((token_class, '', token_text))
                        for token_class, token_text in new_char_tokens[cn1:cn2]:
                            nbuffer.append((token_class, '', token_text))
                    elif ctag == 'delete':
                        for token_class, token_text in old_char_tokens[co1:co2]:
                            obuffer.append((token_class, 'del', token_text))
                    elif ctag == 'insert':
                        for token_class, token_text in new_char_tokens[cn1:cn2]:
                            nbuffer.append((token_class, 'ins', token_text))
                    elif ctag == 'replace':
                        for token_class, token_text in old_char_tokens[co1:co2]:
                            obuffer.append((token_class, 'del', token_text))
                        for token_class, token_text in new_char_tokens[cn1:cn2]:
                            nbuffer.append((token_class, 'ins', token_text))

            old_tokens_result.extend(obuffer)
            new_tokens_result.extend(nbuffer)

    return old_tokens_result, new_tokens_result, similarity


class DiffSet(object):
    """
    An object for parsing the diff result from diffs.DiffProcessor and
    adding highlighting, side by side/unified renderings and line diffs
    """

    HL_REAL = 'REAL' # highlights using original file, slow
    HL_FAST = 'FAST' # highlights using just the line, fast but not correct
                     # in the case of multiline code
    HL_NONE = 'NONE' # no highlighting, fastest

    def __init__(self, highlight_mode=HL_REAL, repo_name=None,
                 source_repo_name=None,
                 source_node_getter=lambda filename: None,
                 target_node_getter=lambda filename: None,
                 source_nodes=None, target_nodes=None,
                 max_file_size_limit=150 * 1024, # files over this size will
                                                 # use fast highlighting
                 comments=None,
                 ):

        self.highlight_mode = highlight_mode
        self.highlighted_filenodes = {}
        self.source_node_getter = source_node_getter
        self.target_node_getter = target_node_getter
        self.source_nodes = source_nodes or {}
        self.target_nodes = target_nodes or {}
        self.repo_name = repo_name
        self.source_repo_name = source_repo_name or repo_name
        self.comments = comments or {}
        self.comments_store = self.comments.copy()
        self.max_file_size_limit = max_file_size_limit

    def render_patchset(self, patchset, source_ref=None, target_ref=None):
        diffset = AttributeDict(dict(
            lines_added=0,
            lines_deleted=0,
            changed_files=0,
            files=[],
            file_stats={},
            limited_diff=isinstance(patchset, LimitedDiffContainer),
            repo_name=self.repo_name,
            source_repo_name=self.source_repo_name,
            source_ref=source_ref,
            target_ref=target_ref,
        ))
        for patch in patchset:
            diffset.file_stats[patch['filename']] = patch['stats']
            filediff = self.render_patch(patch)
            filediff.diffset = diffset
            diffset.files.append(filediff)
            diffset.changed_files += 1
            if not patch['stats']['binary']:
                diffset.lines_added += patch['stats']['added']
                diffset.lines_deleted += patch['stats']['deleted']

        return diffset

    _lexer_cache = {}
    def _get_lexer_for_filename(self, filename, filenode=None):
        # cached because we might need to call it twice for source/target
        if filename not in self._lexer_cache:
            if filenode:
                lexer = filenode.lexer
                extension = filenode.extension
            else:
                lexer = FileNode.get_lexer(filename=filename)
                extension = filename.split('.')[-1]

            lexer = get_custom_lexer(extension) or lexer
            self._lexer_cache[filename] = lexer
        return self._lexer_cache[filename]

    def render_patch(self, patch):
        log.debug('rendering diff for %r' % patch['filename'])

        source_filename = patch['original_filename']
        target_filename = patch['filename']

        source_lexer = plain_text_lexer
        target_lexer = plain_text_lexer

        if not patch['stats']['binary']:
            if self.highlight_mode == self.HL_REAL:
                if (source_filename and patch['operation'] in ('D', 'M')
                    and source_filename not in self.source_nodes):
                        self.source_nodes[source_filename] = (
                            self.source_node_getter(source_filename))

                if (target_filename and patch['operation'] in ('A', 'M')
                    and target_filename not in self.target_nodes):
                        self.target_nodes[target_filename] = (
                            self.target_node_getter(target_filename))

            elif self.highlight_mode == self.HL_FAST:
                source_lexer = self._get_lexer_for_filename(source_filename)
                target_lexer = self._get_lexer_for_filename(target_filename)

        source_file = self.source_nodes.get(source_filename, source_filename)
        target_file = self.target_nodes.get(target_filename, target_filename)

        source_filenode, target_filenode = None, None

        # TODO: dan: FileNode.lexer works on the content of the file - which
        # can be slow - issue #4289 explains a lexer clean up - which once
        # done can allow caching a lexer for a filenode to avoid the file lookup
        if isinstance(source_file, FileNode):
            source_filenode = source_file
            #source_lexer = source_file.lexer
            source_lexer = self._get_lexer_for_filename(source_filename)
            source_file.lexer = source_lexer

        if isinstance(target_file, FileNode):
            target_filenode = target_file
            #target_lexer = target_file.lexer
            target_lexer = self._get_lexer_for_filename(target_filename)
            target_file.lexer = target_lexer

        source_file_path, target_file_path = None, None

        if source_filename != '/dev/null':
            source_file_path = source_filename
        if target_filename != '/dev/null':
            target_file_path = target_filename

        source_file_type = source_lexer.name
        target_file_type = target_lexer.name

        filediff = AttributeDict({
            'source_file_path': source_file_path,
            'target_file_path': target_file_path,
            'source_filenode': source_filenode,
            'target_filenode': target_filenode,
            'source_file_type': target_file_type,
            'target_file_type': source_file_type,
            'patch': {'filename': patch['filename'], 'stats': patch['stats']},
            'operation': patch['operation'],
            'source_mode': patch['stats']['old_mode'],
            'target_mode': patch['stats']['new_mode'],
            'limited_diff': isinstance(patch, LimitedDiffContainer),
            'hunks': [],
            'diffset': self,
        })

        for hunk in patch['chunks'][1:]:
            hunkbit = self.parse_hunk(hunk, source_file, target_file)
            hunkbit.source_file_path = source_file_path
            hunkbit.target_file_path = target_file_path
            filediff.hunks.append(hunkbit)

        left_comments = {}
        if source_file_path in self.comments_store:
            for lineno, comments in self.comments_store[source_file_path].items():
                left_comments[lineno] = comments

        if target_file_path in self.comments_store:
            for lineno, comments in self.comments_store[target_file_path].items():
                left_comments[lineno] = comments
        filediff.left_comments = left_comments

        return filediff

    def parse_hunk(self, hunk, source_file, target_file):
        result = AttributeDict(dict(
            source_start=hunk['source_start'],
            source_length=hunk['source_length'],
            target_start=hunk['target_start'],
            target_length=hunk['target_length'],
            section_header=hunk['section_header'],
            lines=[],
        ))
        before, after = [], []

        for line in hunk['lines']:

            if line['action'] == 'unmod':
                result.lines.extend(
                    self.parse_lines(before, after, source_file, target_file))
                after.append(line)
                before.append(line)
            elif line['action'] == 'add':
                after.append(line)
            elif line['action'] == 'del':
                before.append(line)
            elif line['action'] == 'old-no-nl':
                before.append(line)
            elif line['action'] == 'new-no-nl':
                after.append(line)

        result.lines.extend(
            self.parse_lines(before, after, source_file, target_file))
        result.unified = self.as_unified(result.lines)
        result.sideside = result.lines

        return result

    def parse_lines(self, before_lines, after_lines, source_file, target_file):
        # TODO: dan: investigate doing the diff comparison and fast highlighting
        # on the entire before and after buffered block lines rather than by
        # line, this means we can get better 'fast' highlighting if the context
        # allows it - eg.
        # line 4: """
        # line 5: this gets highlighted as a string
        # line 6: """

        lines = []
        while before_lines or after_lines:
            before, after = None, None
            before_tokens, after_tokens = None, None

            if before_lines:
                before = before_lines.pop(0)
            if after_lines:
                after = after_lines.pop(0)

            original = AttributeDict()
            modified = AttributeDict()

            if before:
                if before['action'] == 'old-no-nl':
                    before_tokens = [('nonl', before['line'])]
                else:
                    before_tokens = self.get_line_tokens(
                        line_text=before['line'],
                        line_number=before['old_lineno'],
                        file=source_file)
                original.lineno = before['old_lineno']
                original.content = before['line']
                original.action = self.action_to_op(before['action'])
                original.comments = self.get_comments_for('old',
                    source_file, before['old_lineno'])

            if after:
                if after['action'] == 'new-no-nl':
                    after_tokens = [('nonl', after['line'])]
                else:
                    after_tokens = self.get_line_tokens(
                        line_text=after['line'], line_number=after['new_lineno'],
                        file=target_file)
                modified.lineno = after['new_lineno']
                modified.content = after['line']
                modified.action = self.action_to_op(after['action'])
                modified.comments = self.get_comments_for('new',
                    target_file, after['new_lineno'])

            # diff the lines
            if before_tokens and after_tokens:
                o_tokens, m_tokens, similarity = tokens_diff(
                    before_tokens, after_tokens)
                original.content = render_tokenstream(o_tokens)
                modified.content = render_tokenstream(m_tokens)
            elif before_tokens:
                original.content = render_tokenstream(
                    [(x[0], '', x[1]) for x in before_tokens])
            elif after_tokens:
                modified.content = render_tokenstream(
                    [(x[0], '', x[1]) for x in after_tokens])

            lines.append(AttributeDict({
                'original': original,
                'modified': modified,
            }))

        return lines

    def get_comments_for(self, version, file, line_number):
        if hasattr(file, 'unicode_path'):
            file = file.unicode_path

        if not isinstance(file, basestring):
            return None

        line_key = {
            'old': 'o',
            'new': 'n',
        }[version] + str(line_number)

        if file in self.comments_store:
            file_comments = self.comments_store[file]
            if line_key in file_comments:
                return file_comments.pop(line_key)

    def get_line_tokens(self, line_text, line_number, file=None):
        filenode = None
        filename = None

        if isinstance(file, basestring):
            filename = file
        elif isinstance(file, FileNode):
            filenode = file
            filename = file.unicode_path

        if self.highlight_mode == self.HL_REAL and filenode:
            lexer = self._get_lexer_for_filename(filename)
            file_size_allowed = file.size < self.max_file_size_limit
            if line_number and file_size_allowed:
                return self.get_tokenized_filenode_line(
                    file, line_number, lexer)

        if self.highlight_mode in (self.HL_REAL, self.HL_FAST) and filename:
            lexer = self._get_lexer_for_filename(filename)
            return list(tokenize_string(line_text, lexer))

        return list(tokenize_string(line_text, plain_text_lexer))

    def get_tokenized_filenode_line(self, filenode, line_number, lexer=None):

        if filenode not in self.highlighted_filenodes:
            tokenized_lines = filenode_as_lines_tokens(filenode, lexer)
            self.highlighted_filenodes[filenode] = tokenized_lines
        return self.highlighted_filenodes[filenode][line_number - 1]

    def action_to_op(self, action):
        return {
            'add': '+',
            'del': '-',
            'unmod': ' ',
            'old-no-nl': ' ',
            'new-no-nl': ' ',
        }.get(action, action)

    def as_unified(self, lines):
        """
        Return a generator that yields the lines of a diff in unified order
        """
        def generator():
            buf = []
            for line in lines:

                if buf and not line.original or line.original.action == ' ':
                    for b in buf:
                        yield b
                    buf = []

                if line.original:
                    if line.original.action == ' ':
                        yield (line.original.lineno, line.modified.lineno,
                               line.original.action, line.original.content,
                               line.original.comments)
                        continue

                    if line.original.action == '-':
                        yield (line.original.lineno, None,
                               line.original.action, line.original.content,
                               line.original.comments)

                    if line.modified.action == '+':
                        buf.append((
                            None, line.modified.lineno,
                            line.modified.action, line.modified.content,
                            line.modified.comments))
                        continue

                if line.modified:
                    yield (None, line.modified.lineno,
                           line.modified.action, line.modified.content,
                           line.modified.comments)

            for b in buf:
                yield b

        return generator()
