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

from rhodecode.model.db import User, UserApiKeys

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, assert_session_flash)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()



def route_path(name, **kwargs):
    return {
        'users':
            ADMIN_PREFIX + '/users',
        'users_data':
            ADMIN_PREFIX + '/users_data',
        'edit_user_auth_tokens':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens',
        'edit_user_auth_tokens_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/new',
        'edit_user_auth_tokens_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/delete',
    }[name].format(**kwargs)


class TestAdminUsersView(TestController):

    def test_auth_tokens_default_user(self):
        self.log_user()
        user = User.get_default_user()
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user.user_id),
            status=302)

    def test_auth_tokens(self):
        self.log_user()

        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user.user_id))
        for token in user.auth_tokens:
            response.mustcontain(token)
            response.mustcontain('never')

    @pytest.mark.parametrize("desc, lifetime", [
        ('forever', -1),
        ('5mins', 60*5),
        ('30days', 60*60*24*30),
    ])
    def test_add_auth_token(self, desc, lifetime, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': desc, 'lifetime': lifetime,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')

        response = response.follow()
        user = User.get(user_id)
        for auth_token in user.auth_tokens:
            response.mustcontain(auth_token)

    def test_delete_auth_token(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id
        keys = user.extra_auth_tokens
        assert 2 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': 'desc', 'lifetime': -1,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')
        response.follow()

        # now delete our key
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 3 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_delete', user_id=user_id),
            {'del_auth_token': keys[0].api_key, 'csrf_token': self.csrf_token})

        assert_session_flash(response, 'Auth token successfully deleted')
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 2 == len(keys)
