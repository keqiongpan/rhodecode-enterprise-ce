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

"""
us in hooks::

    from .helpers import extract_pre_files
    # returns list of dicts with key-val fetched from extra fields
    file_list = extract_pre_files.run(**kwargs)

"""
import re
import collections
import json

from rhodecode.lib import diffs
from rhodecode.lib.vcs.backends.hg.diff import MercurialDiff
from rhodecode.lib.vcs.backends.git.diff import GitDiff
from vcsserver.utils import safe_int


def get_svn_files(repo, vcs_repo, refs):
    txn_id = refs[0]
    files = []

    stdout, stderr = vcs_repo.run_svn_command(
        ['svnlook', 'changed', repo.repo_full_path, '--transaction', txn_id])

    svn_op_to_rc_op = {
        'A': 'A',
        'U': 'M',
        'D': 'D',
    }

    for entry in stdout.splitlines():
        parsed_entry = {
            'raw_diff': '',
            'filename': '',
            'chunks': [],
            'ops': {},
            'file_size': 0
        }

        op = entry[0]
        path = entry[1:].strip()

        rc_op = svn_op_to_rc_op.get(op) or '?'
        parsed_entry['filename'] = path
        parsed_entry['operation'] = rc_op

        if rc_op in ['A', 'M']:

            stdout, stderr = vcs_repo.run_svn_command(
                ['svnlook', 'filesize', repo.repo_full_path, path, '--transaction', txn_id],
                _safe=True
            )

            if "Path '{}' is not a file".format(path.rstrip('/')) in stderr:
                # skip dirs
                continue

            parsed_entry['file_size'] = safe_int(stdout.strip()) or 0

        files.append(parsed_entry)

    return files


def get_hg_files(repo, vcs_repo, refs):
    files = []
    return files


def get_git_files(repo, vcs_repo, refs):
    files = []

    for data in refs:
        # we should now extract commit data
        old_rev = data['old_rev']
        new_rev = data['new_rev']

        if '00000000' in old_rev:
            # new branch, we don't need to extract nothing
            return files

        git_env = dict(data['git_env'])

        cmd = [
            'diff', old_rev, new_rev
        ]

        stdout, stderr = vcs_repo.run_git_command(cmd, extra_env=git_env)
        vcs_diff = GitDiff(stdout)

        diff_processor = diffs.DiffProcessor(vcs_diff, format='newdiff')
        # this is list of dicts with diff information
        # _parsed[0].keys()
        # ['raw_diff', 'old_revision', 'stats', 'original_filename',
        #  'is_limited_diff', 'chunks', 'new_revision', 'operation',
        #  'exceeds_limit', 'filename']
        files = _parsed = diff_processor.prepare()

    return files


def run(*args, **kwargs):
    from rhodecode.model.db import Repository

    vcs_type = kwargs['scm']
    # use temp name then the main one propagated
    repo_name = kwargs.pop('REPOSITORY', None) or kwargs['repository']

    repo = Repository.get_by_repo_name(repo_name)
    vcs_repo = repo.scm_instance(cache=False)

    files = []

    if vcs_type == 'git':
        for rev_data in kwargs['commit_ids']:
            new_environ = dict((k, v) for k, v in rev_data['git_env'])
        files = get_git_files(repo, vcs_repo, kwargs['commit_ids'])

    if vcs_type == 'hg':
        for rev_data in kwargs['commit_ids']:
            new_environ = dict((k, v) for k, v in rev_data['hg_env'])
        files = get_hg_files(repo, vcs_repo, kwargs['commit_ids'])

    if vcs_type == 'svn':
        files = get_svn_files(repo, vcs_repo, kwargs['commit_ids'])

    return files
