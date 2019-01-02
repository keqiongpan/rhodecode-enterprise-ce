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

from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.tests.vcs_operations import (
    Command, _check_proper_hg_push, _check_proper_git_push,
    _add_files, _add_files_and_push)


@pytest.mark.usefixtures("disable_anonymous_user")
class TestVCSOperations(object):

    def test_push_force_hg(self, rc_web_server, tmpdir, user_util):
        repo = user_util.create_repo(repo_type='hg')
        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'hg clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=clone_url)
        _check_proper_hg_push(stdout, stderr)

        # rewrite history, and push with force
        Command(tmpdir.strpath).execute(
            'hg checkout -r 1 && hg commit -m "starting new head"')
        _add_files('hg', tmpdir.strpath, clone_url=clone_url)

        stdout, stderr = Command(tmpdir.strpath).execute(
            'hg push --verbose -f {}'.format(clone_url))

        _check_proper_hg_push(stdout, stderr)

    def test_push_force_git(self, rc_web_server, tmpdir, user_util):
        repo = user_util.create_repo(repo_type='git')
        clone_url = rc_web_server.repo_clone_url(repo.repo_name)
        Command(os.path.dirname(tmpdir.strpath)).execute(
            'git clone', clone_url, tmpdir.strpath)

        stdout, stderr = _add_files_and_push(
            'git', tmpdir.strpath, clone_url=clone_url)
        _check_proper_git_push(stdout, stderr)

        # rewrite history, and push with force
        Command(tmpdir.strpath).execute(
            'git reset --hard HEAD~2')
        stdout, stderr = Command(tmpdir.strpath).execute(
            'git push -f {} master'.format(clone_url))

        assert '(forced update)' in stderr

    def test_push_force_hg_blocked_by_branch_permissions(
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

        # rewrite history, and push with force
        Command(tmpdir.strpath).execute(
            'hg checkout -r 1 && hg commit -m "starting new head"')
        _add_files('hg', tmpdir.strpath, clone_url=clone_url)

        stdout, stderr = Command(tmpdir.strpath).execute(
            'hg push --verbose -f {}'.format(clone_url))

        assert "Branch `default` changes rejected by rule `*`=>branch.push" in stdout
        assert "FORCE PUSH FORBIDDEN" in stdout
        assert "transaction abort" in stdout

    def test_push_force_git_blocked_by_branch_permissions(
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

        # rewrite history, and push with force
        Command(tmpdir.strpath).execute(
            'git reset --hard HEAD~2')
        stdout, stderr = Command(tmpdir.strpath).execute(
            'git push -f {} master'.format(clone_url))

        assert "Branch `master` changes rejected by rule `*`=>branch.push" in stderr
        assert "FORCE PUSH FORBIDDEN" in stderr
        assert "(pre-receive hook declined)" in stderr
