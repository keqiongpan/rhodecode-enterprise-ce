# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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

import os

import mock
import pytest

from rhodecode.controllers.files import FilesController
from rhodecode.lib import helpers as h
from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.ext_json import json
from rhodecode.lib.vcs import nodes
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib.vcs.conf import settings
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.model.db import Repository
from rhodecode.model.scm import ScmModel
from rhodecode.tests import (
    url, TEST_USER_ADMIN_LOGIN, assert_session_flash, assert_not_in_session_flash)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import commit_change

fixture = Fixture()


@pytest.mark.usefixtures("autologin_user", "app")
class TestSideBySideDiff(object):

    def test_diff_side_by_side(self, app, backend, backend_stub):
        f_path = 'test_sidebyside_file.py'
        commit1_content = 'content-25d7e49c18b159446c\n'
        commit2_content = 'content-603d6c72c46d953420\n'
        repo = backend.create_repo()

        commit1 = commit_change(
            repo.repo_name, filename=f_path, content=commit1_content,
            message='A', vcs_type=backend.alias, parent=None, newfile=True)

        commit2 = commit_change(
            repo.repo_name, filename=f_path, content=commit2_content,
            message='B, child of A', vcs_type=backend.alias, parent=commit1)

        compare_url = url(
            'compare_url',
            repo_name=repo.repo_name,
            source_ref_type='rev',
            source_ref=commit1.raw_id,
            target_repo=repo.repo_name,
            target_ref_type='rev',
            target_ref=commit2.raw_id,
            f_path=f_path,
            diffmode='sidebyside')

        response = self.app.get(compare_url)

        response.mustcontain('Expand 1 commit')
        response.mustcontain('1 file changed')

        response.mustcontain(
            'r%s:%s...r%s:%s' % (
            commit1.idx, commit1.short_id, commit2.idx, commit2.short_id))

        response.mustcontain('<strong>{}</strong>'.format(f_path))

    def test_diff_side_by_side_with_empty_file(self, app, backend, backend_stub):
        commits = [
            {'message': 'First commit'},
            {'message': 'Commit with binary',
             'added': [nodes.FileNode('file.empty', content='')]},
        ]
        f_path = 'file.empty'
        repo = backend.create_repo(commits=commits)
        commit1 = repo.get_commit(commit_idx=0)
        commit2 = repo.get_commit(commit_idx=1)

        compare_url = url(
            'compare_url',
            repo_name=repo.repo_name,
            source_ref_type='rev',
            source_ref=commit1.raw_id,
            target_repo=repo.repo_name,
            target_ref_type='rev',
            target_ref=commit2.raw_id,
            f_path=f_path,
            diffmode='sidebyside')

        response = self.app.get(compare_url)

        response.mustcontain('Expand 1 commit')
        response.mustcontain('1 file changed')

        response.mustcontain(
            'r%s:%s...r%s:%s' % (
            commit1.idx, commit1.short_id, commit2.idx, commit2.short_id))

        response.mustcontain('<strong>{}</strong>'.format(f_path))

    def test_diff_sidebyside_two_commits(self, app, backend):
        commit_id_range = {
            'hg': {
                'commits': ['25d7e49c18b159446cadfa506a5cf8ad1cb04067',
                            '603d6c72c46d953420c89d36372f08d9f305f5dd'],
                'changes': '21 files changed: 943 inserted, 288 deleted'
            },
            'git': {
                'commits': ['6fc9270775aaf5544c1deb014f4ddd60c952fcbb',
                            '03fa803d7e9fb14daa9a3089e0d1494eda75d986'],
                'changes': '21 files changed: 943 inserted, 288 deleted'
            },

            'svn': {
                'commits': ['336',
                            '337'],
                'changes': '21 files changed: 943 inserted, 288 deleted'
            },
        }

        commit_info = commit_id_range[backend.alias]
        commit2, commit1 = commit_info['commits']
        file_changes = commit_info['changes']

        compare_url = url(
            'compare_url',
            repo_name=backend.repo_name,
            source_ref_type='rev',
            source_ref=commit2,
            target_repo=backend.repo_name,
            target_ref_type='rev',
            target_ref=commit1,
            diffmode='sidebyside')
        response = self.app.get(compare_url)

        response.mustcontain('Expand 1 commit')
        response.mustcontain(file_changes)

    def test_diff_sidebyside_two_commits_single_file(self, app, backend):
        commit_id_range = {
            'hg': {
                'commits': ['25d7e49c18b159446cadfa506a5cf8ad1cb04067',
                            '603d6c72c46d953420c89d36372f08d9f305f5dd'],
                'changes': '1 file changed: 1 inserted, 1 deleted'
            },
            'git': {
                'commits': ['6fc9270775aaf5544c1deb014f4ddd60c952fcbb',
                            '03fa803d7e9fb14daa9a3089e0d1494eda75d986'],
                'changes': '1 file changed: 1 inserted, 1 deleted'
            },

            'svn': {
                'commits': ['336',
                            '337'],
                'changes': '1 file changed: 1 inserted, 1 deleted'
            },
        }
        f_path = 'docs/conf.py'

        commit_info = commit_id_range[backend.alias]
        commit2, commit1 = commit_info['commits']
        file_changes = commit_info['changes']

        compare_url = url(
            'compare_url',
            repo_name=backend.repo_name,
            source_ref_type='rev',
            source_ref=commit2,
            target_repo=backend.repo_name,
            target_ref_type='rev',
            target_ref=commit1,
            f_path=f_path,
            diffmode='sidebyside')
        response = self.app.get(compare_url)

        response.mustcontain('Expand 1 commit')
        response.mustcontain(file_changes)
