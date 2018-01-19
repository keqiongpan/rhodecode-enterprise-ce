# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
Test suite for making push/pull operations, on specially modified INI files

.. important::

   You must have git >= 1.8.5 for tests to work fine. With 68b939b git started
   to redirect things to stderr instead of stdout.
"""

import os
import pytest

from rhodecode.lib.vcs.backends.git.repository import GitRepository
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.tests import GIT_REPO
from rhodecode.tests.vcs_operations import Command
from .test_vcs_operations import _check_proper_clone, _check_proper_git_push


def test_git_clone_with_small_push_buffer(backend_git, rc_web_server, tmpdir):
    clone_url = rc_web_server.repo_clone_url(GIT_REPO)
    cmd = Command('/tmp')
    stdout, stderr = cmd.execute(
        'git -c http.postBuffer=1024 clone', clone_url, tmpdir.strpath)
    _check_proper_clone(stdout, stderr, 'git')
    cmd.assert_returncode_success()


def test_git_push_with_small_push_buffer(backend_git, rc_web_server, tmpdir):
    empty_repo = backend_git.create_repo()

    clone_url = rc_web_server.repo_clone_url(empty_repo.repo_name)

    cmd = Command(tmpdir.strpath)
    cmd.execute('git clone', clone_url)

    repo = GitRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
    repo.in_memory_commit.add(FileNode('readme.md', content='## Hello'))
    repo.in_memory_commit.commit(
        message='Commit on branch Master',
        author='Automatic test',
        branch='master')

    repo_cmd = Command(repo.path)
    stdout, stderr = repo_cmd.execute(
        'git -c http.postBuffer=1024 push --verbose origin master')
    _check_proper_git_push(stdout, stderr, branch='master')
