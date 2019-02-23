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

import pytest

from rhodecode.model.db import User
from rhodecode.tests import (
    TestController, TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, **kwargs):
    return '/_profiles/{username}'.format(**kwargs)


class TestUsersController(TestController):

    def test_user_profile(self, user_util):
        edit_link_css = '.user-profile .panel-edit'
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        user = user_util.create_user(
            'test-my-user', password='qweqwe', email='testme@rhodecode.org')
        username = user.username

        response = self.app.get(route_path('user_profile', username=username))
        response.mustcontain('testme')
        response.mustcontain('testme@rhodecode.org')
        assert_response = AssertResponse(response)
        assert_response.no_element_exists(edit_link_css)

        # edit should be available to superadmin users
        self.logout_user()
        self.log_user(TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
        response = self.app.get(route_path('user_profile', username=username))
        assert_response = AssertResponse(response)
        assert_response.element_contains(edit_link_css, 'Edit')

    def test_user_profile_not_available(self, user_util):
        user = user_util.create_user()
        username = user.username

        # not logged in, redirect
        self.app.get(route_path('user_profile', username=username), status=302)

        self.log_user()
        # after log-in show
        self.app.get(route_path('user_profile', username=username), status=200)

        # default user, not allowed to show it
        self.app.get(
            route_path('user_profile', username=User.DEFAULT_USER), status=404)

        # actual 404
        self.app.get(route_path('user_profile', username='unknown'), status=404)
