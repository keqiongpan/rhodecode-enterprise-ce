# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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

import pytest

from rhodecode.tests import (
    TestController, url, assert_session_flash, link_to)
from rhodecode.model.db import User, UserGroup
from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture


fixture = Fixture()


class TestAdminUsersGroupsController(TestController):

    def test_regular_user_cannot_see_admin_interfaces(self, user_util):
        user = user_util.create_user(password='qweqwe')
        self.log_user(user.username, 'qweqwe')

        # check if in home view, such user doesn't see the "admin" menus
        response = self.app.get(url('home'))

        assert_response = response.assert_response()

        assert_response.no_element_exists('li.local-admin-repos')
        assert_response.no_element_exists('li.local-admin-repo-groups')
        assert_response.no_element_exists('li.local-admin-user-groups')

        response = self.app.get(url('repos'), status=200)
        response.mustcontain('data: []')

        response = self.app.get(url('repo_groups'), status=200)
        response.mustcontain('data: []')

        response = self.app.get(url('users_groups'), status=200)
        response.mustcontain('data: []')

    def test_regular_user_can_see_admin_interfaces_if_owner(self, user_util):
        user = user_util.create_user(password='qweqwe')
        username = user.username

        repo = user_util.create_repo(owner=username)
        repo_name = repo.repo_name

        repo_group = user_util.create_repo_group(owner=username)
        repo_group_name = repo_group.group_name

        user_group = user_util.create_user_group(owner=username)
        user_group_name = user_group.users_group_name

        self.log_user(username, 'qweqwe')
        # check if in home view, such user doesn't see the "admin" menus
        response = self.app.get(url('home'))

        assert_response = response.assert_response()

        assert_response.one_element_exists('li.local-admin-repos')
        assert_response.one_element_exists('li.local-admin-repo-groups')
        assert_response.one_element_exists('li.local-admin-user-groups')

        # admin interfaces have visible elements
        response = self.app.get(url('repos'), status=200)
        response.mustcontain('"name_raw": "{}"'.format(repo_name))

        response = self.app.get(url('repo_groups'), status=200)
        response.mustcontain('"name_raw": "{}"'.format(repo_group_name))

        response = self.app.get(url('users_groups'), status=200)
        response.mustcontain('"group_name_raw": "{}"'.format(user_group_name))

    def test_regular_user_can_see_admin_interfaces_if_admin_perm(self, user_util):
        user = user_util.create_user(password='qweqwe')
        username = user.username

        repo = user_util.create_repo()
        repo_name = repo.repo_name

        repo_group = user_util.create_repo_group()
        repo_group_name = repo_group.group_name

        user_group = user_util.create_user_group()
        user_group_name = user_group.users_group_name

        user_util.grant_user_permission_to_repo(
            repo, user, 'repository.admin')
        user_util.grant_user_permission_to_repo_group(
            repo_group, user, 'group.admin')
        user_util.grant_user_permission_to_user_group(
            user_group, user, 'usergroup.admin')

        self.log_user(username, 'qweqwe')
        # check if in home view, such user doesn't see the "admin" menus
        response = self.app.get(url('home'))

        assert_response = response.assert_response()

        assert_response.one_element_exists('li.local-admin-repos')
        assert_response.one_element_exists('li.local-admin-repo-groups')
        assert_response.one_element_exists('li.local-admin-user-groups')

        # admin interfaces have visible elements
        response = self.app.get(url('repos'), status=200)
        response.mustcontain('"name_raw": "{}"'.format(repo_name))

        response = self.app.get(url('repo_groups'), status=200)
        response.mustcontain('"name_raw": "{}"'.format(repo_group_name))

        response = self.app.get(url('users_groups'), status=200)
        response.mustcontain('"group_name_raw": "{}"'.format(user_group_name))
