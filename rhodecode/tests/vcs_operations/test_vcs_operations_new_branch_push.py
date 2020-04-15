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


import os
import pytest

from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.tests.vcs_operations import (
    Command, _check_proper_hg_push, _check_proper_git_push, _add_files_and_push)


@pytest.mark.usefixtures("disable_anonymous_user")
class TestVCSOperations(object):

    def test_push_new_branch_hg(self, rc_web_server, tmpdir, user_util):
        repo = user_util.create_repo(repo_type='hg')
        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'hg clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url)
        _check_proper_hg_push(stdout, stderr)

        # start new branch, and push file into it
        Command(tmpdir.strpath).execute(
            'hg branch dev && hg commit -m "starting dev branch"')
        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url, target_branch='dev',
            new_branch=True)

        _check_proper_hg_push(stdout, stderr)

    def test_push_new_branch_git(self, rc_web_server, tmpdir, user_util):
        repo = user_util.create_repo(repo_type='git')
        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'git clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url)
        _check_proper_git_push(stdout, stderr)

        # start new branch, and push file into it
        Command(tmpdir.strpath).execute('git checkout -b dev')
        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url, target_branch='dev',
            new_branch=True)

        _check_proper_git_push(stdout, stderr, branch='dev')

    def test_push_new_branch_hg_with_branch_permissions_no_force_push(
            self, rc_web_server, tmpdir, user_util, branch_permission_setter):
        repo = user_util.create_repo(repo_type='hg')
        repo_name = repo.repo_name
        username = TEST_USER_ADMIN_LOGIN
        branch_permission_setter(repo_name, username, permission='branch.push')

        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'hg clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url)
        _check_proper_hg_push(stdout, stderr)

        # start new branch, and push file into it
        Command(tmpdir.strpath).execute(
            'hg branch dev && hg commit -m "starting dev branch"')
        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url, target_branch='dev',
            new_branch=True)

        _check_proper_hg_push(stdout, stderr)

    def test_push_new_branch_git_with_branch_permissions_no_force_push(
            self, rc_web_server, tmpdir, user_util, branch_permission_setter):
        repo = user_util.create_repo(repo_type='git')
        repo_name = repo.repo_name
        username = TEST_USER_ADMIN_LOGIN
        branch_permission_setter(repo_name, username, permission='branch.push')

        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'git clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url)
        _check_proper_git_push(stdout, stderr)

        # start new branch, and push file into it
        Command(tmpdir.strpath).execute('git checkout -b dev')
        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url, target_branch='dev',
            new_branch=True)

        _check_proper_git_push(stdout, stderr, branch='dev')
