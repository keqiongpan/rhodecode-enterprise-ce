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

import pytest

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.tests import (
    TestController, TEST_USER_ADMIN_LOGIN,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'my_account':
            ADMIN_PREFIX + '/my_account/profile',
    }[name].format(**kwargs)


class TestMyAccountProfile(TestController):

    def test_my_account(self):
        self.log_user()
        response = self.app.get(route_path('my_account'))

        response.mustcontain(TEST_USER_ADMIN_LOGIN)
        response.mustcontain('href="/_admin/my_account/edit"')
        response.mustcontain('Photo')

    def test_my_account_regular_user(self):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        response = self.app.get(route_path('my_account'))

        response.mustcontain(TEST_USER_REGULAR_LOGIN)
        response.mustcontain('href="/_admin/my_account/edit"')
        response.mustcontain('Photo')
