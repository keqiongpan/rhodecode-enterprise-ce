# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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
from rhodecode.model.db import User
from rhodecode.tests import (
    TestController, TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS, assert_session_flash)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'my_account_auth_tokens':
            ADMIN_PREFIX + '/my_account/auth_tokens',
        'my_account_auth_tokens_add':
            ADMIN_PREFIX + '/my_account/auth_tokens/new',
        'my_account_auth_tokens_delete':
            ADMIN_PREFIX + '/my_account/auth_tokens/delete',
    }[name].format(**kwargs)


class TestMyAccountAuthTokens(TestController):

    def test_my_account_auth_tokens(self):
        usr = self.log_user('test_regular2', 'test12')
        user = User.get(usr['user_id'])
        response = self.app.get(route_path('my_account_auth_tokens'))
        for token in user.auth_tokens:
            response.mustcontain(token)
            response.mustcontain('never')

    def test_my_account_add_auth_tokens_wrong_csrf(self, user_util):
        user = user_util.create_user(password='qweqwe')
        self.log_user(user.username, 'qweqwe')

        self.app.post(
            route_path('my_account_auth_tokens_add'),
            {'description': 'desc', 'lifetime': -1}, status=403)

    @pytest.mark.parametrize("desc, lifetime", [
        ('forever', -1),
        ('5mins', 60*5),
        ('30days', 60*60*24*30),
    ])
    def test_my_account_add_auth_tokens(self, desc, lifetime, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        response = self.app.post(
            route_path('my_account_auth_tokens_add'),
            {'description': desc, 'lifetime': lifetime,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')

        response = response.follow()
        user = User.get(user_id)
        for auth_token in user.auth_tokens:
            response.mustcontain(auth_token)

    def test_my_account_delete_auth_token(self, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        user = User.get(user_id)
        keys = user.get_auth_tokens()
        assert 2 == len(keys)

        response = self.app.post(
            route_path('my_account_auth_tokens_add'),
            {'description': 'desc', 'lifetime': -1,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')
        response.follow()

        user = User.get(user_id)
        keys = user.get_auth_tokens()
        assert 3 == len(keys)

        response = self.app.post(
            route_path('my_account_auth_tokens_delete'),
            {'del_auth_token': keys[0].user_api_key_id, 'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully deleted')

        user = User.get(user_id)
        keys = user.auth_tokens
        assert 2 == len(keys)
