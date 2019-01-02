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
from rhodecode.model.user_group import UserGroupModel
from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, **kwargs):
    return '/_profile_user_group/{user_group_name}'.format(**kwargs)


class TestUsersController(TestController):

    def test_user_group_profile(self, user_util):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        user, usergroup = user_util.create_user_with_group()

        response = self.app.get(route_path('profile_user_group', user_group_name=usergroup.users_group_name))
        response.mustcontain(usergroup.users_group_name)
        response.mustcontain(user.username)

    def test_user_can_check_own_group(self, user_util):
        user = user_util.create_user(
            TEST_USER_REGULAR_LOGIN, password=TEST_USER_REGULAR_PASS, email='testme@rhodecode.org')
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        usergroup = user_util.create_user_group(owner=user)
        response = self.app.get(route_path('profile_user_group', user_group_name=usergroup.users_group_name))
        response.mustcontain(usergroup.users_group_name)
        response.mustcontain(user.username)

    def test_user_can_not_check_other_group(self, user_util):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        user_group = user_util.create_user_group()
        UserGroupModel().grant_user_permission(user_group, self._get_logged_user(), 'usergroup.none')
        response = self.app.get(route_path('profile_user_group', user_group_name=user_group.users_group_name), status=404)
        assert response.status_code == 404

    def test_another_user_can_check_if_he_is_in_group(self, user_util):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        user = user_util.create_user(
            'test-my-user', password='qweqwe', email='testme@rhodecode.org')
        user_group = user_util.create_user_group()
        UserGroupModel().add_user_to_group(user_group, user)
        UserGroupModel().grant_user_permission(user_group, self._get_logged_user(), 'usergroup.read')
        response = self.app.get(route_path('profile_user_group', user_group_name=user_group.users_group_name))
        response.mustcontain(user_group.users_group_name)
        response.mustcontain(user.username)

    def test_with_anonymous_user(self, user_util):
        user = user_util.create_user(
            'test-my-user', password='qweqwe', email='testme@rhodecode.org')
        user_group = user_util.create_user_group()
        UserGroupModel().add_user_to_group(user_group, user)
        response = self.app.get(route_path('profile_user_group', user_group_name=user_group.users_group_name), status=302)
        assert response.status_code == 302