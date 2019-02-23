# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

from rhodecode.tests import (
    TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.vcs_operations import (
    Command, _check_proper_hg_push, _check_proper_git_push, _add_files_and_push)


@pytest.mark.usefixtures("disable_anonymous_user")
class TestVCSOperations(object):

    @pytest.mark.parametrize('username, password', [
        (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS),
        (TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS),
    ])
    @pytest.mark.parametrize('branch_perm', [
        'branch.none',
        'branch.merge',
        'branch.push',
        'branch.push_force',
    ])
    def test_push_to_protected_branch_fails_with_message_hg(
            self, rc_web_server, tmpdir, branch_perm, user_util,
            branch_permission_setter, username, password):
        repo = user_util.create_repo(repo_type='hg')
        repo_name = repo.repo_name
        branch_permission_setter(repo_name, username, permission=branch_perm)

        clone_url = rc_web_server.repo_clone_url(
            repo.repo_name, user=username, passwd=password)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'hg clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url)
        if branch_perm in ['branch.push', 'branch.push_force']:
            _check_proper_hg_push(stdout, stderr)
        else:
            msg = "Branch `default` changes rejected by rule `*`=>{}".format(branch_perm)
            assert msg in stdout
            assert "transaction abort" in stdout

    @pytest.mark.parametrize('username, password', [
        (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS),
        (TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS),
    ])
    @pytest.mark.parametrize('branch_perm', [
        'branch.none',
        'branch.merge',
        'branch.push',
        'branch.push_force',
    ])
    def test_push_to_protected_branch_fails_with_message_git(
            self, rc_web_server, tmpdir, branch_perm, user_util,
            branch_permission_setter, username, password):
        repo = user_util.create_repo(repo_type='git')
        repo_name = repo.repo_name
        branch_permission_setter(repo_name, username, permission=branch_perm)

        clone_url = rc_web_server.repo_clone_url(
            repo.repo_name, user=username, passwd=password)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'git clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url)
        if branch_perm in ['branch.push', 'branch.push_force']:
            _check_proper_git_push(stdout, stderr)
        else:
            msg = "Branch `master` changes rejected by rule `*`=>{}".format(branch_perm)
            assert msg in stderr
            assert "(pre-receive hook declined)" in stderr
