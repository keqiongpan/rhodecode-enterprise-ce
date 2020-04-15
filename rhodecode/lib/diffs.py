# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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


"""
Set of diffing helpers, previously part of vcs
"""

import os
import re
import bz2
import gzip
import time

import collections
import difflib
import logging
import cPickle as pickle
from itertools import tee, imap

from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.nodes import FileNode, SubModuleNode
from rhodecode.lib.utils2 import safe_unicode, safe_str

log = logging.getLogger(__name__)

# define max context, a file with more than this numbers of lines is unusable
# in browser anyway
MAX_CONTEXT = 20 * 1024
DEFAULT_CONTEXT = 3


def get_diff_context(request):
    return MAX_CONTEXT if request.GET.get('fullcontext', '') == '1' else DEFAULT_CONTEXT


def get_diff_whitespace_flag(request):
    return request.GET.get('ignorews', '') == '1'


class OPS(object):
    ADD = 'A'
    MOD = 'M'
    DEL = 'D'


def get_gitdiff(filenode_old, filenode_new, ignore_whitespace=True, context=3):
    """
    Returns git style diff between given ``filenode_old`` and ``filenode_new``.

    :param ignore_whitespace: ignore whitespaces in diff
    """
    # make sure we pass in default context
    context = context or 3
    # protect against IntOverflow when passing HUGE context
    if context > MAX_CONTEXT:
        context = MAX_CONTEXT

    submodules = filter(lambda o: isinstance(o, SubModuleNode),
                        [filenode_new, filenode_old])
    if submodules:
        return ''

    for filenode in (filenode_old, filenode_new):
        if not isinstance(filenode, FileNode):
            raise VCSError(
                "Given object should be FileNode object, not %s"
                % filenode.__class__)

    repo = filenode_new.commit.repository
    old_commit = filenode_old.commit or repo.EMPTY_COMMIT
    new_commit = filenode_new.commit

    vcs_gitdiff = repo.get_diff(
        old_commit, new_commit, filenode_new.path,
        ignore_whitespace, context, path1=filenode_old.path)
    return vcs_gitdiff

NEW_FILENODE = 1
DEL_FILENODE = 2
MOD_FILENODE = 3
RENAMED_FILENODE = 4
COPIED_FILENODE = 5
CHMOD_FILENODE = 6
BIN_FILENODE = 7


class LimitedDiffContainer(object):

    def __init__(self, diff_limit, cur_diff_size, diff):
        self.diff = diff
        self.diff_limit = diff_limit
        self.cur_diff_size = cur_diff_size

    def __getitem__(self, key):
        return self.diff.__getitem__(key)

    def __iter__(self):
        for l in self.diff:
            yield l


class Action(object):
    """
    Contains constants for the action value of the lines in a parsed diff.
    """

    ADD = 'add'
    DELETE = 'del'
    UNMODIFIED = 'unmod'

    CONTEXT = 'context'
    OLD_NO_NL = 'old-no-nl'
    NEW_NO_NL = 'new-no-nl'


class DiffProcessor(object):
    """
    Give it a unified or git diff and it returns a list of the files that were
    mentioned in the diff together with a dict of meta information that
    can be used to render it in a HTML template.

    .. note:: Unicode handling

       The original diffs are a byte sequence and can contain filenames
       in mixed encodings. This class generally returns `unicode` objects
       since the result is intended for presentation to the user.

    """
    _chunk_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)')
    _newline_marker = re.compile(r'^\\ No newline at end of file')

    # used for inline highlighter word split
    _token_re = re.compile(r'()(&gt;|&lt;|&amp;|\W+?)')

    # collapse ranges of commits over given number
    _collapse_commits_over = 5

    def __init__(self, diff, format='gitdiff', diff_limit=None,
                 file_limit=None, show_full_diff=True):
        """
        :param diff: A `Diff` object representing a diff from a vcs backend
        :param format: format of diff passed, `udiff` or `gitdiff`
        :param diff_limit: define the size of diff that is considered "big"
            based on that parameter cut off will be triggered, set to None
            to show full diff
        """
        self._diff = diff
        self._format = format
        self.adds = 0
        self.removes = 0
        # calculate diff size
        self.diff_limit = diff_limit
        self.file_limit = file_limit
        self.show_full_diff = show_full_diff
        self.cur_diff_size = 0
        self.parsed = False
        self.parsed_diff = []

        log.debug('Initialized DiffProcessor with %s mode', format)
        if format == 'gitdiff':
            self.differ = self._highlight_line_difflib
            self._parser = self._parse_gitdiff
        else:
            self.differ = self._highlight_line_udiff
            self._parser = self._new_parse_gitdiff

    def _copy_iterator(self):
        """
        make a fresh copy of generator, we should not iterate thru
        an original as it's needed for repeating operations on
        this instance of DiffProcessor
        """
        self.__udiff, iterator_copy = tee(self.__udiff)
        return iterator_copy

    def _escaper(self, string):
        """
        Escaper for diff escapes special chars and checks the diff limit

        :param string:
        """
        self.cur_diff_size += len(string)

        if not self.show_full_diff and (self.cur_diff_size > self.diff_limit):
            raise DiffLimitExceeded('Diff Limit Exceeded')

        return string \
            .replace('&', '&amp;')\
            .replace('<', '&lt;')\
            .replace('>', '&gt;')

    def _line_counter(self, l):
        """
        Checks each line and bumps total adds/removes for this diff

        :param l:
        """
        if l.startswith('+') and not l.startswith('+++'):
            self.adds += 1
        elif l.startswith('-') and not l.startswith('---'):
            self.removes += 1
        return safe_unicode(l)

    def _highlight_line_difflib(self, line, next_):
        """
        Highlight inline changes in both lines.
        """

        if line['action'] == Action.DELETE:
            old, new = line, next_
        else:
            old, new = next_, line

        oldwords = self._token_re.split(old['line'])
        newwords = self._token_re.split(new['line'])
        sequence = difflib.SequenceMatcher(None, oldwords, newwords)

        oldfragments, newfragments = [], []
        for tag, i1, i2, j1, j2 in sequence.get_opcodes():
            oldfrag = ''.join(oldwords[i1:i2])
            newfrag = ''.join(newwords[j1:j2])
            if tag != 'equal':
                if oldfrag:
                    oldfrag = '<del>%s</del>' % oldfrag
                if newfrag:
                    newfrag = '<ins>%s</ins>' % newfrag
            oldfragments.append(oldfrag)
            newfragments.append(newfrag)

        old['line'] = "".join(oldfragments)
        new['line'] = "".join(newfragments)

    def _highlight_line_udiff(self, line, next_):
        """
        Highlight inline changes in both lines.
        """
        start = 0
        limit = min(len(line['line']), len(next_['line']))
        while start < limit and line['line'][start] == next_['line'][start]:
            start += 1
        end = -1
        limit -= start
        while -end <= limit and line['line'][end] == next_['line'][end]:
            end -= 1
        end += 1
        if start or end:
            def do(l):
                last = end + len(l['line'])
                if l['action'] == Action.ADD:
                    tag = 'ins'
                else:
                    tag = 'del'
                l['line'] = '%s<%s>%s</%s>%s' % (
                    l['line'][:start],
                    tag,
                    l['line'][start:last],
                    tag,
                    l['line'][last:]
                )
            do(line)
            do(next_)

    def _clean_line(self, line, command):
        if command in ['+', '-', ' ']:
            # only modify the line if it's actually a diff thing
            line = line[1:]
        return line

    def _parse_gitdiff(self, inline_diff=True):
        _files = []
        diff_container = lambda arg: arg

        for chunk in self._diff.chunks():
            head = chunk.header

            diff = imap(self._escaper, self.diff_splitter(chunk.diff))
            raw_diff = chunk.raw
            limited_diff = False
            exceeds_limit = False

            op = None
            stats = {
                'added': 0,
                'deleted': 0,
                'binary': False,
                'ops': {},
            }

            if head['deleted_file_mode']:
                op = OPS.DEL
                stats['binary'] = True
                stats['ops'][DEL_FILENODE] = 'deleted file'

            elif head['new_file_mode']:
                op = OPS.ADD
                stats['binary'] = True
                stats['ops'][NEW_FILENODE] = 'new file %s' % head['new_file_mode']
            else:  # modify operation, can be copy, rename or chmod

                # CHMOD
                if head['new_mode'] and head['old_mode']:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][CHMOD_FILENODE] = (
                        'modified file chmod %s => %s' % (
                            head['old_mode'], head['new_mode']))
                # RENAME
                if head['rename_from'] != head['rename_to']:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][RENAMED_FILENODE] = (
                        'file renamed from %s to %s' % (
                            head['rename_from'], head['rename_to']))
                # COPY
                if head.get('copy_from') and head.get('copy_to'):
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][COPIED_FILENODE] = (
                        'file copied from %s to %s' % (
                            head['copy_from'], head['copy_to']))

                # If our new parsed headers didn't match anything fallback to
                # old style detection
                if op is None:
                    if not head['a_file'] and head['b_file']:
                        op = OPS.ADD
                        stats['binary'] = True
                        stats['ops'][NEW_FILENODE] = 'new file'

                    elif head['a_file'] and not head['b_file']:
                        op = OPS.DEL
                        stats['binary'] = True
                        stats['ops'][DEL_FILENODE] = 'deleted file'

                # it's not ADD not DELETE
                if op is None:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][MOD_FILENODE] = 'modified file'

            # a real non-binary diff
            if head['a_file'] or head['b_file']:
                try:
                    raw_diff, chunks, _stats = self._parse_lines(diff)
                    stats['binary'] = False
                    stats['added'] = _stats[0]
                    stats['deleted'] = _stats[1]
                    # explicit mark that it's a modified file
                    if op == OPS.MOD:
                        stats['ops'][MOD_FILENODE] = 'modified file'
                    exceeds_limit = len(raw_diff) > self.file_limit

                    # changed from _escaper function so we validate size of
                    # each file instead of the whole diff
                    # diff will hide big files but still show small ones
                    # from my tests, big files are fairly safe to be parsed
                    # but the browser is the bottleneck
                    if not self.show_full_diff and exceeds_limit:
                        raise DiffLimitExceeded('File Limit Exceeded')

                except DiffLimitExceeded:
                    diff_container = lambda _diff: \
                        LimitedDiffContainer(
                            self.diff_limit, self.cur_diff_size, _diff)

                    exceeds_limit = len(raw_diff) > self.file_limit
                    limited_diff = True
                    chunks = []

            else:  # GIT format binary patch, or possibly empty diff
                if head['bin_patch']:
                    # we have operation already extracted, but we mark simply
                    # it's a diff we wont show for binary files
                    stats['ops'][BIN_FILENODE] = 'binary diff hidden'
                chunks = []

            if chunks and not self.show_full_diff and op == OPS.DEL:
                # if not full diff mode show deleted file contents
                # TODO: anderson: if the view is not too big, there is no way
                # to see the content of the file
                chunks = []

            chunks.insert(0, [{
                                  'old_lineno': '',
                                  'new_lineno': '',
                                  'action': Action.CONTEXT,
                                  'line': msg,
                              } for _op, msg in stats['ops'].iteritems()
                              if _op not in [MOD_FILENODE]])

            _files.append({
                'filename': safe_unicode(head['b_path']),
                'old_revision': head['a_blob_id'],
                'new_revision': head['b_blob_id'],
                'chunks': chunks,
                'raw_diff': safe_unicode(raw_diff),
                'operation': op,
                'stats': stats,
                'exceeds_limit': exceeds_limit,
                'is_limited_diff': limited_diff,
            })

        sorter = lambda info: {OPS.ADD: 0, OPS.MOD: 1,
                               OPS.DEL: 2}.get(info['operation'])

        if not inline_diff:
            return diff_container(sorted(_files, key=sorter))

        # highlight inline changes
        for diff_data in _files:
            for chunk in diff_data['chunks']:
                lineiter = iter(chunk)
                try:
                    while 1:
                        line = lineiter.next()
                        if line['action'] not in (
                                Action.UNMODIFIED, Action.CONTEXT):
                            nextline = lineiter.next()
                            if nextline['action'] in ['unmod', 'context'] or \
                               nextline['action'] == line['action']:
                                continue
                            self.differ(line, nextline)
                except StopIteration:
                    pass

        return diff_container(sorted(_files, key=sorter))

    def _check_large_diff(self):
        log.debug('Diff exceeds current diff_limit of %s', self.diff_limit)
        if not self.show_full_diff and (self.cur_diff_size > self.diff_limit):
            raise DiffLimitExceeded('Diff Limit `%s` Exceeded', self.diff_limit)

    # FIXME: NEWDIFFS: dan: this replaces _parse_gitdiff
    def _new_parse_gitdiff(self, inline_diff=True):
        _files = []

        # this can be overriden later to a LimitedDiffContainer type
        diff_container = lambda arg: arg

        for chunk in self._diff.chunks():
            head = chunk.header
            log.debug('parsing diff %r', head)

            raw_diff = chunk.raw
            limited_diff = False
            exceeds_limit = False

            op = None
            stats = {
                'added': 0,
                'deleted': 0,
                'binary': False,
                'old_mode': None,
                'new_mode': None,
                'ops': {},
            }
            if head['old_mode']:
                stats['old_mode'] = head['old_mode']
            if head['new_mode']:
                stats['new_mode'] = head['new_mode']
            if head['b_mode']:
                stats['new_mode'] = head['b_mode']

            # delete file
            if head['deleted_file_mode']:
                op = OPS.DEL
                stats['binary'] = True
                stats['ops'][DEL_FILENODE] = 'deleted file'

            # new file
            elif head['new_file_mode']:
                op = OPS.ADD
                stats['binary'] = True
                stats['old_mode'] = None
                stats['new_mode'] = head['new_file_mode']
                stats['ops'][NEW_FILENODE] = 'new file %s' % head['new_file_mode']

            # modify operation, can be copy, rename or chmod
            else:
                # CHMOD
                if head['new_mode'] and head['old_mode']:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][CHMOD_FILENODE] = (
                        'modified file chmod %s => %s' % (
                            head['old_mode'], head['new_mode']))

                # RENAME
                if head['rename_from'] != head['rename_to']:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['renamed'] = (head['rename_from'], head['rename_to'])
                    stats['ops'][RENAMED_FILENODE] = (
                        'file renamed from %s to %s' % (
                            head['rename_from'], head['rename_to']))
                # COPY
                if head.get('copy_from') and head.get('copy_to'):
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['copied'] = (head['copy_from'], head['copy_to'])
                    stats['ops'][COPIED_FILENODE] = (
                        'file copied from %s to %s' % (
                            head['copy_from'], head['copy_to']))

                # If our new parsed headers didn't match anything fallback to
                # old style detection
                if op is None:
                    if not head['a_file'] and head['b_file']:
                        op = OPS.ADD
                        stats['binary'] = True
                        stats['new_file'] = True
                        stats['ops'][NEW_FILENODE] = 'new file'

                    elif head['a_file'] and not head['b_file']:
                        op = OPS.DEL
                        stats['binary'] = True
                        stats['ops'][DEL_FILENODE] = 'deleted file'

                # it's not ADD not DELETE
                if op is None:
                    op = OPS.MOD
                    stats['binary'] = True
                    stats['ops'][MOD_FILENODE] = 'modified file'

            # a real non-binary diff
            if head['a_file'] or head['b_file']:
                # simulate splitlines, so we keep the line end part
                diff = self.diff_splitter(chunk.diff)

                # append each file to the diff size
                raw_chunk_size = len(raw_diff)

                exceeds_limit = raw_chunk_size > self.file_limit
                self.cur_diff_size += raw_chunk_size

                try:
                    # Check each file instead of the whole diff.
                    # Diff will hide big files but still show small ones.
                    # From the tests big files are fairly safe to be parsed
                    # but the browser is the bottleneck.
                    if not self.show_full_diff and exceeds_limit:
                        log.debug('File `%s` exceeds current file_limit of %s',
                                  safe_unicode(head['b_path']), self.file_limit)
                        raise DiffLimitExceeded(
                            'File Limit %s Exceeded', self.file_limit)

                    self._check_large_diff()

                    raw_diff, chunks, _stats = self._new_parse_lines(diff)
                    stats['binary'] = False
                    stats['added'] = _stats[0]
                    stats['deleted'] = _stats[1]
                    # explicit mark that it's a modified file
                    if op == OPS.MOD:
                        stats['ops'][MOD_FILENODE] = 'modified file'

                except DiffLimitExceeded:
                    diff_container = lambda _diff: \
                        LimitedDiffContainer(
                            self.diff_limit, self.cur_diff_size, _diff)

                    limited_diff = True
                    chunks = []

            else:  # GIT format binary patch, or possibly empty diff
                if head['bin_patch']:
                    # we have operation already extracted, but we mark simply
                    # it's a diff we wont show for binary files
                    stats['ops'][BIN_FILENODE] = 'binary diff hidden'
                chunks = []

            # Hide content of deleted node by setting empty chunks
            if chunks and not self.show_full_diff and op == OPS.DEL:
                # if not full diff mode show deleted file contents
                # TODO: anderson: if the view is not too big, there is no way
                # to see the content of the file
                chunks = []

            chunks.insert(
                0, [{'old_lineno': '',
                     'new_lineno': '',
                     'action': Action.CONTEXT,
                     'line': msg,
                     } for _op, msg in stats['ops'].iteritems()
                    if _op not in [MOD_FILENODE]])

            original_filename = safe_unicode(head['a_path'])
            _files.append({
                'original_filename': original_filename,
                'filename': safe_unicode(head['b_path']),
                'old_revision': head['a_blob_id'],
                'new_revision': head['b_blob_id'],
                'chunks': chunks,
                'raw_diff': safe_unicode(raw_diff),
                'operation': op,
                'stats': stats,
                'exceeds_limit': exceeds_limit,
                'is_limited_diff': limited_diff,
            })

        sorter = lambda info: {OPS.ADD: 0, OPS.MOD: 1,
                               OPS.DEL: 2}.get(info['operation'])

        return diff_container(sorted(_files, key=sorter))

    # FIXME: NEWDIFFS: dan: this gets replaced by _new_parse_lines
    def _parse_lines(self, diff_iter):
        """
        Parse the diff an return data for the template.
        """

        stats = [0, 0]
        chunks = []
        raw_diff = []

        try:
            line = diff_iter.next()

            while line:
                raw_diff.append(line)
                lines = []
                chunks.append(lines)

                match = self._chunk_re.match(line)

                if not match:
                    break

                gr = match.groups()
                (old_line, old_end,
                 new_line, new_end) = [int(x or 1) for x in gr[:-1]]
                old_line -= 1
                new_line -= 1

                context = len(gr) == 5
                old_end += old_line
                new_end += new_line

                if context:
                    # skip context only if it's first line
                    if int(gr[0]) > 1:
                        lines.append({
                            'old_lineno': '...',
                            'new_lineno': '...',
                            'action':     Action.CONTEXT,
                            'line':       line,
                        })

                line = diff_iter.next()

                while old_line < old_end or new_line < new_end:
                    command = ' '
                    if line:
                        command = line[0]

                    affects_old = affects_new = False

                    # ignore those if we don't expect them
                    if command in '#@':
                        continue
                    elif command == '+':
                        affects_new = True
                        action = Action.ADD
                        stats[0] += 1
                    elif command == '-':
                        affects_old = True
                        action = Action.DELETE
                        stats[1] += 1
                    else:
                        affects_old = affects_new = True
                        action = Action.UNMODIFIED

                    if not self._newline_marker.match(line):
                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno':   affects_old and old_line or '',
                            'new_lineno':   affects_new and new_line or '',
                            'action':       action,
                            'line':         self._clean_line(line, command)
                        })
                        raw_diff.append(line)

                    line = diff_iter.next()

                    if self._newline_marker.match(line):
                        # we need to append to lines, since this is not
                        # counted in the line specs of diff
                        lines.append({
                            'old_lineno':   '...',
                            'new_lineno':   '...',
                            'action':       Action.CONTEXT,
                            'line':         self._clean_line(line, command)
                        })

        except StopIteration:
            pass
        return ''.join(raw_diff), chunks, stats

    # FIXME: NEWDIFFS: dan: this replaces _parse_lines
    def _new_parse_lines(self, diff_iter):
        """
        Parse the diff an return data for the template.
        """

        stats = [0, 0]
        chunks = []
        raw_diff = []

        try:
            line = diff_iter.next()

            while line:
                raw_diff.append(line)
                # match header e.g @@ -0,0 +1 @@\n'
                match = self._chunk_re.match(line)

                if not match:
                    break

                gr = match.groups()
                (old_line, old_end,
                 new_line, new_end) = [int(x or 1) for x in gr[:-1]]

                lines = []
                hunk = {
                    'section_header': gr[-1],
                    'source_start': old_line,
                    'source_length': old_end,
                    'target_start': new_line,
                    'target_length': new_end,
                    'lines': lines,
                }
                chunks.append(hunk)

                old_line -= 1
                new_line -= 1

                context = len(gr) == 5
                old_end += old_line
                new_end += new_line

                line = diff_iter.next()

                while old_line < old_end or new_line < new_end:
                    command = ' '
                    if line:
                        command = line[0]

                    affects_old = affects_new = False

                    # ignore those if we don't expect them
                    if command in '#@':
                        continue
                    elif command == '+':
                        affects_new = True
                        action = Action.ADD
                        stats[0] += 1
                    elif command == '-':
                        affects_old = True
                        action = Action.DELETE
                        stats[1] += 1
                    else:
                        affects_old = affects_new = True
                        action = Action.UNMODIFIED

                    if not self._newline_marker.match(line):
                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno':   affects_old and old_line or '',
                            'new_lineno':   affects_new and new_line or '',
                            'action':       action,
                            'line':         self._clean_line(line, command)
                        })
                    raw_diff.append(line)

                    line = diff_iter.next()

                    if self._newline_marker.match(line):
                        # we need to append to lines, since this is not
                        # counted in the line specs of diff
                        if affects_old:
                            action = Action.OLD_NO_NL
                        elif affects_new:
                            action = Action.NEW_NO_NL
                        else:
                            raise Exception('invalid context for no newline')

                        lines.append({
                            'old_lineno':   None,
                            'new_lineno':   None,
                            'action':       action,
                            'line':         self._clean_line(line, command)
                        })

        except StopIteration:
            pass

        return ''.join(raw_diff), chunks, stats

    def _safe_id(self, idstring):
        """Make a string safe for including in an id attribute.

        The HTML spec says that id attributes 'must begin with
        a letter ([A-Za-z]) and may be followed by any number
        of letters, digits ([0-9]), hyphens ("-"), underscores
        ("_"), colons (":"), and periods (".")'. These regexps
        are slightly over-zealous, in that they remove colons
        and periods unnecessarily.

        Whitespace is transformed into underscores, and then
        anything which is not a hyphen or a character that
        matches \w (alphanumerics and underscore) is removed.

        """
        # Transform all whitespace to underscore
        idstring = re.sub(r'\s', "_", '%s' % idstring)
        # Remove everything that is not a hyphen or a member of \w
        idstring = re.sub(r'(?!-)\W', "", idstring).lower()
        return idstring

    @classmethod
    def diff_splitter(cls, string):
        """
        Diff split that emulates .splitlines() but works only on \n
        """
        if not string:
            return
        elif string == '\n':
            yield u'\n'
        else:

            has_newline = string.endswith('\n')
            elements = string.split('\n')
            if has_newline:
                # skip last element as it's empty string from newlines
                elements = elements[:-1]

            len_elements = len(elements)

            for cnt, line in enumerate(elements, start=1):
                last_line = cnt == len_elements
                if last_line and not has_newline:
                    yield safe_unicode(line)
                else:
                    yield safe_unicode(line) + '\n'

    def prepare(self, inline_diff=True):
        """
        Prepare the passed udiff for HTML rendering.

        :return: A list of dicts with diff information.
        """
        parsed = self._parser(inline_diff=inline_diff)
        self.parsed = True
        self.parsed_diff = parsed
        return parsed

    def as_raw(self, diff_lines=None):
        """
        Returns raw diff as a byte string
        """
        return self._diff.raw

    def as_html(self, table_class='code-difftable', line_class='line',
                old_lineno_class='lineno old', new_lineno_class='lineno new',
                code_class='code', enable_comments=False, parsed_lines=None):
        """
        Return given diff as html table with customized css classes
        """
        # TODO(marcink): not sure how to pass in translator
        # here in an efficient way, leave the _ for proper gettext extraction
        _ = lambda s: s

        def _link_to_if(condition, label, url):
            """
            Generates a link if condition is meet or just the label if not.
            """

            if condition:
                return '''<a href="%(url)s" class="tooltip"
                title="%(title)s">%(label)s</a>''' % {
                    'title': _('Click to select line'),
                    'url': url,
                    'label': label
                }
            else:
                return label
        if not self.parsed:
            self.prepare()

        diff_lines = self.parsed_diff
        if parsed_lines:
            diff_lines = parsed_lines

        _html_empty = True
        _html = []
        _html.append('''<table class="%(table_class)s">\n''' % {
            'table_class': table_class
        })

        for diff in diff_lines:
            for line in diff['chunks']:
                _html_empty = False
                for change in line:
                    _html.append('''<tr class="%(lc)s %(action)s">\n''' % {
                        'lc': line_class,
                        'action': change['action']
                    })
                    anchor_old_id = ''
                    anchor_new_id = ''
                    anchor_old = "%(filename)s_o%(oldline_no)s" % {
                        'filename': self._safe_id(diff['filename']),
                        'oldline_no': change['old_lineno']
                    }
                    anchor_new = "%(filename)s_n%(oldline_no)s" % {
                        'filename': self._safe_id(diff['filename']),
                        'oldline_no': change['new_lineno']
                    }
                    cond_old = (change['old_lineno'] != '...' and
                                change['old_lineno'])
                    cond_new = (change['new_lineno'] != '...' and
                                change['new_lineno'])
                    if cond_old:
                        anchor_old_id = 'id="%s"' % anchor_old
                    if cond_new:
                        anchor_new_id = 'id="%s"' % anchor_new

                    if change['action'] != Action.CONTEXT:
                        anchor_link = True
                    else:
                        anchor_link = False

                    ###########################################################
                    # COMMENT ICONS
                    ###########################################################
                    _html.append('''\t<td class="add-comment-line"><span class="add-comment-content">''')

                    if enable_comments and change['action'] != Action.CONTEXT:
                        _html.append('''<a href="#"><span class="icon-comment-add"></span></a>''')

                    _html.append('''</span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>\n''')

                    ###########################################################
                    # OLD LINE NUMBER
                    ###########################################################
                    _html.append('''\t<td %(a_id)s class="%(olc)s">''' % {
                        'a_id': anchor_old_id,
                        'olc': old_lineno_class
                    })

                    _html.append('''%(link)s''' % {
                        'link': _link_to_if(anchor_link, change['old_lineno'],
                                            '#%s' % anchor_old)
                    })
                    _html.append('''</td>\n''')
                    ###########################################################
                    # NEW LINE NUMBER
                    ###########################################################

                    _html.append('''\t<td %(a_id)s class="%(nlc)s">''' % {
                        'a_id': anchor_new_id,
                        'nlc': new_lineno_class
                    })

                    _html.append('''%(link)s''' % {
                        'link': _link_to_if(anchor_link, change['new_lineno'],
                                            '#%s' % anchor_new)
                    })
                    _html.append('''</td>\n''')
                    ###########################################################
                    # CODE
                    ###########################################################
                    code_classes = [code_class]
                    if (not enable_comments or
                            change['action'] == Action.CONTEXT):
                        code_classes.append('no-comment')
                    _html.append('\t<td class="%s">' % ' '.join(code_classes))
                    _html.append('''\n\t\t<pre>%(code)s</pre>\n''' % {
                        'code': change['line']
                    })

                    _html.append('''\t</td>''')
                    _html.append('''\n</tr>\n''')
        _html.append('''</table>''')
        if _html_empty:
            return None
        return ''.join(_html)

    def stat(self):
        """
        Returns tuple of added, and removed lines for this instance
        """
        return self.adds, self.removes

    def get_context_of_line(
            self, path, diff_line=None, context_before=3, context_after=3):
        """
        Returns the context lines for the specified diff line.

        :type diff_line: :class:`DiffLineNumber`
        """
        assert self.parsed, "DiffProcessor is not initialized."

        if None not in diff_line:
            raise ValueError(
                "Cannot specify both line numbers: {}".format(diff_line))

        file_diff = self._get_file_diff(path)
        chunk, idx = self._find_chunk_line_index(file_diff, diff_line)

        first_line_to_include = max(idx - context_before, 0)
        first_line_after_context = idx + context_after + 1
        context_lines = chunk[first_line_to_include:first_line_after_context]

        line_contents = [
            _context_line(line) for line in context_lines
            if _is_diff_content(line)]
        # TODO: johbo: Interim fixup, the diff chunks drop the final newline.
        # Once they are fixed, we can drop this line here.
        if line_contents:
            line_contents[-1] = (
                line_contents[-1][0], line_contents[-1][1].rstrip('\n') + '\n')
        return line_contents

    def find_context(self, path, context, offset=0):
        """
        Finds the given `context` inside of the diff.

        Use the parameter `offset` to specify which offset the target line has
        inside of the given `context`. This way the correct diff line will be
        returned.

        :param offset: Shall be used to specify the offset of the main line
            within the given `context`.
        """
        if offset < 0 or offset >= len(context):
            raise ValueError(
                "Only positive values up to the length of the context "
                "minus one are allowed.")

        matches = []
        file_diff = self._get_file_diff(path)

        for chunk in file_diff['chunks']:
            context_iter = iter(context)
            for line_idx, line in enumerate(chunk):
                try:
                    if _context_line(line) == context_iter.next():
                        continue
                except StopIteration:
                    matches.append((line_idx, chunk))
                context_iter = iter(context)

        # Increment position and triger StopIteration
        # if we had a match at the end
        line_idx += 1
        try:
            context_iter.next()
        except StopIteration:
            matches.append((line_idx, chunk))

        effective_offset = len(context) - offset
        found_at_diff_lines = [
            _line_to_diff_line_number(chunk[idx - effective_offset])
            for idx, chunk in matches]

        return found_at_diff_lines

    def _get_file_diff(self, path):
        for file_diff in self.parsed_diff:
            if file_diff['filename'] == path:
                break
        else:
            raise FileNotInDiffException("File {} not in diff".format(path))
        return file_diff

    def _find_chunk_line_index(self, file_diff, diff_line):
        for chunk in file_diff['chunks']:
            for idx, line in enumerate(chunk):
                if line['old_lineno'] == diff_line.old:
                    return chunk, idx
                if line['new_lineno'] == diff_line.new:
                    return chunk, idx
        raise LineNotInDiffException(
            "The line {} is not part of the diff.".format(diff_line))


def _is_diff_content(line):
    return line['action'] in (
        Action.UNMODIFIED, Action.ADD, Action.DELETE)


def _context_line(line):
    return (line['action'], line['line'])


DiffLineNumber = collections.namedtuple('DiffLineNumber', ['old', 'new'])


def _line_to_diff_line_number(line):
    new_line_no = line['new_lineno'] or None
    old_line_no = line['old_lineno'] or None
    return DiffLineNumber(old=old_line_no, new=new_line_no)


class FileNotInDiffException(Exception):
    """
    Raised when the context for a missing file is requested.

    If you request the context for a line in a file which is not part of the
    given diff, then this exception is raised.
    """


class LineNotInDiffException(Exception):
    """
    Raised when the context for a missing line is requested.

    If you request the context for a line in a file and this line is not
    part of the given diff, then this exception is raised.
    """


class DiffLimitExceeded(Exception):
    pass


# NOTE(marcink): if diffs.mako change, probably this
# needs a bump to next version
CURRENT_DIFF_VERSION = 'v4'


def _cleanup_cache_file(cached_diff_file):
    # cleanup file to not store it "damaged"
    try:
        os.remove(cached_diff_file)
    except Exception:
        log.exception('Failed to cleanup path %s', cached_diff_file)


def _get_compression_mode(cached_diff_file):
    mode = 'bz2'
    if 'mode:plain' in cached_diff_file:
        mode = 'plain'
    elif 'mode:gzip' in cached_diff_file:
        mode = 'gzip'
    return mode


def cache_diff(cached_diff_file, diff, commits):
    compression_mode = _get_compression_mode(cached_diff_file)

    struct = {
        'version': CURRENT_DIFF_VERSION,
        'diff': diff,
        'commits': commits
    }

    start = time.time()
    try:
        if compression_mode == 'plain':
            with open(cached_diff_file, 'wb') as f:
                pickle.dump(struct, f)
        elif compression_mode == 'gzip':
            with gzip.GzipFile(cached_diff_file, 'wb') as f:
                pickle.dump(struct, f)
        else:
            with bz2.BZ2File(cached_diff_file, 'wb') as f:
                pickle.dump(struct, f)
    except Exception:
        log.warn('Failed to save cache', exc_info=True)
        _cleanup_cache_file(cached_diff_file)

    log.debug('Saved diff cache under %s in %.4fs', cached_diff_file, time.time() - start)


def load_cached_diff(cached_diff_file):
    compression_mode = _get_compression_mode(cached_diff_file)

    default_struct = {
        'version': CURRENT_DIFF_VERSION,
        'diff': None,
        'commits': None
    }

    has_cache = os.path.isfile(cached_diff_file)
    if not has_cache:
        log.debug('Reading diff cache file failed %s', cached_diff_file)
        return default_struct

    data = None

    start = time.time()
    try:
        if compression_mode == 'plain':
            with open(cached_diff_file, 'rb') as f:
                data = pickle.load(f)
        elif compression_mode == 'gzip':
            with gzip.GzipFile(cached_diff_file, 'rb') as f:
                data = pickle.load(f)
        else:
            with bz2.BZ2File(cached_diff_file, 'rb') as f:
                data = pickle.load(f)
    except Exception:
        log.warn('Failed to read diff cache file', exc_info=True)

    if not data:
        data = default_struct

    if not isinstance(data, dict):
        # old version of data ?
        data = default_struct

    # check version
    if data.get('version') != CURRENT_DIFF_VERSION:
        # purge cache
        _cleanup_cache_file(cached_diff_file)
        return default_struct

    log.debug('Loaded diff cache from %s in %.4fs', cached_diff_file, time.time() - start)

    return data


def generate_diff_cache_key(*args):
    """
    Helper to generate a cache key using arguments
    """
    def arg_mapper(input_param):
        input_param = safe_str(input_param)
        # we cannot allow '/' in arguments since it would allow
        # subdirectory usage
        input_param.replace('/', '_')
        return input_param or None  # prevent empty string arguments

    return '_'.join([
        '{}' for i in range(len(args))]).format(*map(arg_mapper, args))


def diff_cache_exist(cache_storage, *args):
    """
    Based on all generated arguments check and return a cache path
    """
    args = list(args) + ['mode:gzip']
    cache_key = generate_diff_cache_key(*args)
    cache_file_path = os.path.join(cache_storage, cache_key)
    # prevent path traversal attacks using some param that have e.g '../../'
    if not os.path.abspath(cache_file_path).startswith(cache_storage):
        raise ValueError('Final path must be within {}'.format(cache_storage))

    return cache_file_path
