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
import mock

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import check_password
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel
from rhodecode.tests import assert_session_flash
from rhodecode.tests.fixture import Fixture, TestController, error_function

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'home': '/',
        'my_account_password':
            ADMIN_PREFIX + '/my_account/password',
    }[name].format(**kwargs)


test_user_1 = 'testme'
test_user_1_password = '0jd83nHNS/d23n'


class TestMyAccountPassword(TestController):
    def test_valid_change_password(self, user_util):
        new_password = 'my_new_valid_password'
        user = user_util.create_user(password=test_user_1_password)
        self.log_user(user.username, test_user_1_password)

        form_data = [
            ('current_password', test_user_1_password),
            ('__start__', 'new_password:mapping'),
            ('new_password', new_password),
            ('new_password-confirm', new_password),
            ('__end__', 'new_password:mapping'),
            ('csrf_token', self.csrf_token),
        ]
        response = self.app.post(route_path('my_account_password'), form_data).follow()
        assert 'Successfully updated password' in response

        # check_password depends on user being in session
        Session().add(user)
        try:
            assert check_password(new_password, user.password)
        finally:
            Session().expunge(user)

    @pytest.mark.parametrize('current_pw, new_pw, confirm_pw', [
        ('', 'abcdef123', 'abcdef123'),
        ('wrong_pw', 'abcdef123', 'abcdef123'),
        (test_user_1_password, test_user_1_password, test_user_1_password),
        (test_user_1_password, '', ''),
        (test_user_1_password, 'abcdef123', ''),
        (test_user_1_password, '', 'abcdef123'),
        (test_user_1_password, 'not_the', 'same_pw'),
        (test_user_1_password, 'short', 'short'),
    ])
    def test_invalid_change_password(self, current_pw, new_pw, confirm_pw,
                                     user_util):
        user = user_util.create_user(password=test_user_1_password)
        self.log_user(user.username, test_user_1_password)

        form_data = [
            ('current_password', current_pw),
            ('__start__', 'new_password:mapping'),
            ('new_password', new_pw),
            ('new_password-confirm', confirm_pw),
            ('__end__', 'new_password:mapping'),
            ('csrf_token', self.csrf_token),
        ]
        response = self.app.post(route_path('my_account_password'), form_data)

        assert_response = response.assert_response()
        assert assert_response.get_elements('.error-block')

    @mock.patch.object(UserModel, 'update_user', error_function)
    def test_invalid_change_password_exception(self, user_util):
        user = user_util.create_user(password=test_user_1_password)
        self.log_user(user.username, test_user_1_password)

        form_data = [
            ('current_password', test_user_1_password),
            ('__start__', 'new_password:mapping'),
            ('new_password', '123456'),
            ('new_password-confirm', '123456'),
            ('__end__', 'new_password:mapping'),
            ('csrf_token', self.csrf_token),
        ]
        response = self.app.post(route_path('my_account_password'), form_data)
        assert_session_flash(
            response, 'Error occurred during update of user password')

    def test_password_is_updated_in_session_on_password_change(self, user_util):
        old_password = 'abcdef123'
        new_password = 'abcdef124'

        user = user_util.create_user(password=old_password)
        session = self.log_user(user.username, old_password)
        old_password_hash = session['password']

        form_data = [
            ('current_password', old_password),
            ('__start__', 'new_password:mapping'),
            ('new_password', new_password),
            ('new_password-confirm', new_password),
            ('__end__', 'new_password:mapping'),
            ('csrf_token', self.csrf_token),
        ]
        self.app.post(route_path('my_account_password'), form_data)

        response = self.app.get(route_path('home'))
        session = response.get_session_from_response()
        new_password_hash = session['rhodecode_user']['password']

        assert old_password_hash != new_password_hash