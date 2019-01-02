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

from rhodecode.lib import helpers as h
from rhodecode.tests import (
    TestController, clear_cache_regions,
    TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'login': ADMIN_PREFIX + '/login',
        'logout': ADMIN_PREFIX + '/logout',
        'register': ADMIN_PREFIX + '/register',
        'reset_password':
            ADMIN_PREFIX + '/password_reset',
        'reset_password_confirmation':
            ADMIN_PREFIX + '/password_reset_confirmation',

        'admin_permissions_application':
            ADMIN_PREFIX + '/permissions/application',
        'admin_permissions_application_update':
            ADMIN_PREFIX + '/permissions/application/update',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestPasswordReset(TestController):

    @pytest.mark.parametrize(
        'pwd_reset_setting, show_link, show_reset', [
            ('hg.password_reset.enabled', True, True),
            ('hg.password_reset.hidden', False, True),
            ('hg.password_reset.disabled', False, False),
        ])
    def test_password_reset_settings(
            self, pwd_reset_setting, show_link, show_reset):
        clear_cache_regions()
        self.log_user(TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
        params = {
            'csrf_token': self.csrf_token,
            'anonymous': 'True',
            'default_register': 'hg.register.auto_activate',
            'default_register_message': '',
            'default_password_reset': pwd_reset_setting,
            'default_extern_activate': 'hg.extern_activate.auto',
        }
        resp = self.app.post(route_path('admin_permissions_application_update'), params=params)
        self.logout_user()

        login_page = self.app.get(route_path('login'))
        asr_login = AssertResponse(login_page)
        index_page = self.app.get(h.route_path('home'))
        asr_index = AssertResponse(index_page)

        if show_link:
            asr_login.one_element_exists('a.pwd_reset')
            asr_index.one_element_exists('a.pwd_reset')
        else:
            asr_login.no_element_exists('a.pwd_reset')
            asr_index.no_element_exists('a.pwd_reset')

        response = self.app.get(route_path('reset_password'))
        
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
        self.app.post(route_path('admin_permissions_application_update'), params=params)
        self.logout_user()

        response = self.app.post(
            route_path('reset_password'), {'email': 'lisa@rhodecode.com',}
        )
        response = response.follow()
        response.mustcontain('Password reset is disabled.')
