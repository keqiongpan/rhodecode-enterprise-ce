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

from rhodecode.config.routing import ADMIN_PREFIX
from rhodecode.tests import (
    TestController, clear_all_caches, url,
    TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()

# Hardcode URLs because we don't have a request object to use
# pyramids URL generation methods.
index_url = '/'
login_url = ADMIN_PREFIX + '/login'
logut_url = ADMIN_PREFIX + '/logout'
register_url = ADMIN_PREFIX + '/register'
pwd_reset_url = ADMIN_PREFIX + '/password_reset'
pwd_reset_confirm_url = ADMIN_PREFIX + '/password_reset_confirmation'


class TestPasswordReset(TestController):

    @pytest.mark.parametrize(
        'pwd_reset_setting, show_link, show_reset', [
            ('hg.password_reset.enabled', True, True),
            ('hg.password_reset.hidden', False, True),
            ('hg.password_reset.disabled', False, False),
        ])
    def test_password_reset_settings(
            self, pwd_reset_setting, show_link, show_reset):
        clear_all_caches()
        self.log_user(TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
        params = {
            'csrf_token': self.csrf_token,
            'anonymous': 'True',
            'default_register': 'hg.register.auto_activate',
            'default_register_message': '',
            'default_password_reset': pwd_reset_setting,
            'default_extern_activate': 'hg.extern_activate.auto',
        }
        resp = self.app.post(url('admin_permissions_application'), params=params)
        self.logout_user()

        login_page = self.app.get(login_url)
        asr_login = AssertResponse(login_page)
        index_page = self.app.get(index_url)
        asr_index = AssertResponse(index_page)

        if show_link:
            asr_login.one_element_exists('a.pwd_reset')
            asr_index.one_element_exists('a.pwd_reset')
        else:
            asr_login.no_element_exists('a.pwd_reset')
            asr_index.no_element_exists('a.pwd_reset')

        response = self.app.get(pwd_reset_url)
        
        assert_response = AssertResponse(response)
        if show_reset:
            response.mustcontain('Send password reset email')
            assert_response.one_element_exists('#email')
            assert_response.one_element_exists('#send')
        else:
            response.mustcontain('Password reset is disabled.')
            assert_response.no_element_exists('#email')
            assert_response.no_element_exists('#send')

    def test_password_form_disabled(self):
        self.log_user(TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
        params = {
            'csrf_token': self.csrf_token,
            'anonymous': 'True',
            'default_register': 'hg.register.auto_activate',
            'default_register_message': '',
            'default_password_reset': 'hg.password_reset.disabled',
            'default_extern_activate': 'hg.extern_activate.auto',
        }
        self.app.post(url('admin_permissions_application'), params=params)
        self.logout_user()

        response = self.app.post(
            pwd_reset_url, {'email': 'lisa@rhodecode.com',}
        )
        response = response.follow()
        response.mustcontain('Password reset is disabled.')
